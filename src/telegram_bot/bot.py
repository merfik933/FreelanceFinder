import telebot
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
import time

from db import db

from .projects_filters.filter_manager import FilterManager

class TelegramBot:
    def __init__(self, token, admin_password):
        self.bot = telebot.TeleBot(token)
        self.token = token
        self.admin_password = admin_password

        self.MAX_MESSAGE_LENGTH = 4096
        self.MAX_DESCRIPTION_LENGTH = 2048

        self.filter_manager = FilterManager()

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
            self.filter_manager.toggle_enabled(call.from_user.id)
            self.bot.answer_callback_query(call.id, "Фільтр змінено")
            self.bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=self.get_filter_settings_markup(call.from_user.id)
            )

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("edit_skills"))
        def edit_skills_handler(call):
            page = int(call.data.split(":")[1])
            skills = list(self.filter_manager.skills.items())
            skills_per_page = 10
            start = page * skills_per_page
            end = start + skills_per_page
            page_skills = skills[start:end]
            selected_skills = self.filter_manager.get_selected_skills(call.from_user.id)

            markup = telebot.types.InlineKeyboardMarkup(row_width=2)

            buttons = []
            for skill_id, name in page_skills:
                is_selected = int(skill_id) in selected_skills
                btn_text = f"✅ {name}" if is_selected else name
                buttons.append(telebot.types.InlineKeyboardButton(
                    btn_text, callback_data=f"toggle_skill:{page}:{skill_id}"
                ))
            for i in range(0, len(buttons), 2):
                markup.add(*buttons[i:i+2])

            nav_buttons = []
            if start > 0:
                nav_buttons.append(telebot.types.InlineKeyboardButton("⬅️", callback_data=f"edit_skills:{page-1}"))
            if end < len(skills):
                nav_buttons.append(telebot.types.InlineKeyboardButton("➡️", callback_data=f"edit_skills:{page+1}"))
            if nav_buttons:
                markup.row(*nav_buttons)

            markup.add(telebot.types.InlineKeyboardButton("🔄 Скинути", callback_data=f"reset_skills:{page}"))
            markup.add(telebot.types.InlineKeyboardButton("❌ Вийти", callback_data="delete_message"))

            self.bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="🛠️ <b>Список категорій:</b>",
                reply_markup=markup,
                parse_mode="HTML"
            )

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("toggle_skill"))
        def toggle_skill_handler(call):
            skill_id_str = call.data.split(":")[2]
            skill_id = int(skill_id_str)
            self.filter_manager.toggle_skill(call.from_user.id, skill_id)
            self.bot.answer_callback_query(call.id, "Змінено")
            edit_skills_handler(call)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("reset_skills"))
        def reset_skills_handler(call):
            self.filter_manager.reset_skills(call.from_user.id)
            self.bot.answer_callback_query(call.id, "Скинуто")
            edit_skills_handler(call)

    def send_projects(self, project_id):
        project = db.get_record("projects", project_id)
        if project is None:
            raise ValueError(f"Project {project_id} not found in database")

        skill_ids = {
            relation["skill_id"]
            for relation in db.get_records("project_skills", project_id=project_id)
        }
        project["skills"] = sorted(
            (skill for skill in db.get_records("skills") if skill["id"] in skill_ids),
            key=lambda skill: skill["name"],
        )

        user = db.get_record("users", role="admin")
        if not user:
            return
        if not self.filter_manager.is_project_allowed(project, user["telegram_id"]):
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
        skills_list = [skill.get('name', '') for skill in project.get('skills', [])]
        skills = f"\n🛠️: {', '.join(skills_list)}" if skills_list else ""
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

        message = f"{name}{skills}{budget}{description}{published}{url}"

        if len(message) > self.MAX_MESSAGE_LENGTH:
            message = message[:self.MAX_MESSAGE_LENGTH] + "…"

        return message

    def get_filter_settings_markup(self, user_id):
        enabled = self.filter_manager.get_filters(user_id)["enabled"]
        action = "Вимкнути" if enabled else "Увімкнути"

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(f"🔄 {action} фільтр", callback_data="toggle_filter"))
        markup.add(telebot.types.InlineKeyboardButton("🛠️ Обрати скіли", callback_data="edit_skills:0"))
        markup.add(telebot.types.InlineKeyboardButton("❌ Вийти", callback_data="delete_message"))

        return markup

    def run(self):
        while True:
            try:
                self.bot.polling(none_stop=True, interval=0)
            except Exception as e:
                time.sleep(5)
