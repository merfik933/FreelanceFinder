import telebot
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import time

from db import db

from .projects_filters import filter_manager
from .projects_tagging.tag_manager import get_project_tag

class TelegramBot:
    def __init__(self, token, admin_password):
        self.bot = telebot.TeleBot(token)
        self.token = token
        self.admin_password = admin_password

        self.MAX_MESSAGE_LENGTH = 4096
        self.MAX_DESCRIPTION_LENGTH = 2048

        self._register_handlers()

    def _register_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def start(message):
            self.bot.send_message(message.chat.id, "Welcome to the bot!")

        @self.bot.message_handler(commands=['admin'])
        def admin(message):
            if message.text == f"/admin {self.admin_password}":
                db.add_record("users", {"telegram_id": message.from_user.id,
                                        "username": message.from_user.username, "role": "admin"})
                self.bot.send_message(message.chat.id, "You are an admin.")
            else:
                self.bot.send_message(message.chat.id, "Invalid password.")

        @self.bot.message_handler(commands=['id'])
        def send_id(message):
            self.bot.send_message(message.chat.id, f"Your ID: {message.chat.id}")

        @self.bot.message_handler(commands=['filters'])
        def filters_command(message):
            user = db.get_record("users", telegram_id=message.from_user.id)
            if not user or user.get("role") != "admin":
                return

            filter_settings_markup = self.get_filter_settings_markup(message.from_user.id)
            self.bot.send_message(
                message.chat.id,
                "Налаштування фільтрів",
                reply_markup=filter_settings_markup
            )

        @self.bot.callback_query_handler(func=lambda call: call.data == "delete_message")
        def delete_message_handler(call):
            self.bot.delete_message(call.message.chat.id, call.message.message_id)

        @self.bot.callback_query_handler(func=lambda call: call.data == "toggle_filter")
        def toggle_filter_handler(call):
            filter_manager.toggle_enabled(call.from_user.id)
            self.bot.answer_callback_query(call.id, "Фільтр змінено")
            self.bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=self.get_filter_settings_markup(call.from_user.id)
            )

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("edit_source_categories"))
        def edit_source_categories_handler(call):
            page = int(call.data.split(":")[1])
            source_categories = list(filter_manager.get_source_categories().items())
            source_categories_per_page = 10
            start = page * source_categories_per_page
            end = start + source_categories_per_page
            page_source_categories = source_categories[start:end]
            selected_source_categories = filter_manager.get_selected_source_categories(call.from_user.id)

            markup = telebot.types.InlineKeyboardMarkup(row_width=2)

            buttons = []
            for source_category_id, name in page_source_categories:
                is_selected = int(source_category_id) in selected_source_categories
                btn_text = f"✅ {name}" if is_selected else name
                buttons.append(telebot.types.InlineKeyboardButton(
                    btn_text, callback_data=f"toggle_source_category:{page}:{source_category_id}"
                ))
            for i in range(0, len(buttons), 2):
                markup.add(*buttons[i:i+2])

            nav_buttons = []
            if start > 0:
                nav_buttons.append(telebot.types.InlineKeyboardButton("⬅️", callback_data=f"edit_source_categories:{page-1}"))
            if end < len(source_categories):
                nav_buttons.append(telebot.types.InlineKeyboardButton("➡️", callback_data=f"edit_source_categories:{page+1}"))
            if nav_buttons:
                markup.row(*nav_buttons)

            markup.add(telebot.types.InlineKeyboardButton("🔄 Скинути", callback_data=f"reset_source_categories:{page}"))
            markup.add(telebot.types.InlineKeyboardButton("❌ Вийти", callback_data="delete_message"))

            self.bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="🛠️ <b>Список категорій:</b>",
                reply_markup=markup,
                parse_mode="HTML"
            )

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_source_category"))
        def toggle_source_category_handler(call):
            source_category_id_str = call.data.split(":")[2]
            source_category_id = int(source_category_id_str)
            filter_manager.toggle_source_category(call.from_user.id, source_category_id)
            self.bot.answer_callback_query(call.id, "Змінено")
            edit_source_categories_handler(call)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("reset_source_categories"))
        def reset_source_categories_handler(call):
            filter_manager.reset_source_categories(call.from_user.id)
            self.bot.answer_callback_query(call.id, "Скинуто")
            edit_source_categories_handler(call)

    def send_projects(self, project_id):
        project = db.get_record("projects", project_id)
        if project is None:
            raise ValueError(f"Project {project_id} not found in database")

        source_category_ids = {
            relation["source_category_id"]
            for relation in db.get_records("project_source_categories", project_id=project_id)
        }
        project["source_categories"] = sorted(
            (source_category for source_category in db.get_records("source_categories") if source_category["id"] in source_category_ids),
            key=lambda source_category: source_category["name"],
        )

        user = db.get_record("users", role="admin")
        if not user:
            return
        if not filter_manager.is_project_allowed(project, user["telegram_id"]):
            return

        message = self.format_project_message(project)

        try:
            self.bot.send_message(
                user["telegram_id"],
                message,
                parse_mode='HTML',
                disable_web_page_preview=True,
            )
            time.sleep(1.1)
        except Exception as e:
            print(f"Error sending message: {e}")
            raise

    def format_project_message(self, project: dict) -> str:
        name = f"<b>{project['name']}</b>"
        source_categories_list = [source_category.get('name', '') for source_category in project.get('source_categories', [])]
        source_categories = f"\n🛠️: {', '.join(source_categories_list)}" if source_categories_list else ""
        tag = get_project_tag(project)
        tags = f"\n🏷️: {tag}" if tag else ""
        budget = ""
        if project.get('budget_amount') is not None:
            budget = f"\n💰 {project['budget_amount']} {project.get('budget_currency') or ''}"
        description = project.get('description') or ""
        if len(description) > self.MAX_DESCRIPTION_LENGTH:
            description = description[:self.MAX_DESCRIPTION_LENGTH] + "…"
        description = f"\n\n{description}"
        published_at = project.get('published_at', '')
        try:
            dt = datetime.fromtimestamp(published_at, timezone.utc).astimezone(ZoneInfo("Europe/Warsaw"))
            published = f"\n\n🕒 {dt.strftime('%H:%M %d.%m.%Y')}"
        except Exception:
            published = f"\n\n🕒 {published_at}"
        url = f"\n🔗{project['url']}"

        message = f"{name}{source_categories}{tags}{budget}{description}{published}{url}"

        if len(message) > self.MAX_MESSAGE_LENGTH:
            message = message[:self.MAX_MESSAGE_LENGTH] + "…"

        return message

    def get_filter_settings_markup(self, user_id):
        enabled = filter_manager.get_filters(user_id)["enabled"]
        action = "Вимкнути" if enabled else "Увімкнути"

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(f"🔄 {action} фільтр", callback_data="toggle_filter"))
        markup.add(telebot.types.InlineKeyboardButton("🛠️ Обрати категорії", callback_data="edit_source_categories:0"))
        markup.add(telebot.types.InlineKeyboardButton("❌ Вийти", callback_data="delete_message"))

        return markup

    def run(self):
        while True:
            try:
                self.bot.polling(none_stop=True, interval=0)
            except Exception as e:
                time.sleep(5)
