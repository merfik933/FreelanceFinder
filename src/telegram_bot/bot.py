import telebot
from datetime import datetime

from .projects_filters.filter_manager import FilterManager

class TelegramBot:
    def __init__(self, token, admin_id):
        self.bot = telebot.TeleBot(token)
        self.token = token
        self.admin_id = admin_id

        self.MAX_MESSAGE_LENGTH = 4096
        self.MAX_DESCRIPTION_LENGTH = 2048

        self.filter_manager = FilterManager()
        
        self._register_handlers()

    def _register_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def start(message):
            self.bot.send_message(message.chat.id, "Welcome to the bot!")

        @self.bot.message_handler(commands=['id'])
        def send_id(message):
            self.bot.send_message(message.chat.id, f"Your ID: {message.chat.id}")    

        @self.bot.message_handler(commands=['filters'])
        def filters_command(message):
            if message.chat.id != self.admin_id:
                return
            filter_settings_markup = self.get_filter_settings_markup()
            self.bot.send_message(
                message.chat.id, 
                "Налаштування фільтрів", 
                reply_markup=filter_settings_markup
            )

        @self.bot.callback_query_handler(func=lambda call: call.data == "delete_message")
        def delete_message_handler(call):
            self.bot.delete_message(call.message.chat.id, call.message.message_id)

        @self.bot.callback_query_handler(func=lambda call: call.data == "toggle_mode")
        def toggle_mode_handler(call):
            self.filter_manager.toggle_filter_mode()
            self.bot.answer_callback_query(call.id, "Режим змінено")
            self.bot.edit_message_reply_markup(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                reply_markup=self.get_filter_settings_markup()
            )

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("edit_skills"))
        def edit_skills_handler(call):
            page = int(call.data.split(":")[1])
            skills = list(self.filter_manager.skills.items())
            skills_per_page = 10
            start = page * skills_per_page
            end = start + skills_per_page
            page_skills = skills[start:end]
            selected_skills = self.filter_manager.get_selected_skills()

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
            if skill_id in self.filter_manager.get_selected_skills():
                self.filter_manager.remove_skill(skill_id)
            else:
                self.filter_manager.add_skill(skill_id)
            self.bot.answer_callback_query(call.id, "Змінено")
            edit_skills_handler(call)

        @self.bot.callback_query_handler(func=lambda call: call.data.startswith("reset_skills"))
        def reset_skills_handler(call):
            self.filter_manager.filters["skills"] = []
            self.filter_manager._save_filters()
            self.bot.answer_callback_query(call.id, "Скинуто")
            edit_skills_handler(call)

    def send_projects(self, project):
        message = self.format_project_message(project)
        try: 
            self.bot.send_message(self.admin_id, message, parse_mode='HTML', disable_web_page_preview=True)
        except Exception as e:
            print(f"Error sending message: {e}")
        
    def format_project_message(self, project: dict) -> str:
        title = f"<b>{project['title']}</b>"
        url = f"\n🔗{project['url']}"
        description = project.get('description') or ""
        if len(description) > self.MAX_DESCRIPTION_LENGTH:
            description = description[:self.MAX_DESCRIPTION_LENGTH] + "…"
        description = f"\n\n{description}"
        skills_list = [skill.get('name', '') for skill in project.get('skills', [])]
        skills = f"\n\n🛠️ Навички: {', '.join(skills_list)}" if skills_list else ""
        budget = ""
        if project.get('budget') and project['budget'].get('amount'):
            budget = f"\n💰 {project['budget']['amount']} {project['budget']['currency']}"
        published_at = project.get('published_at', '')
        try:
            dt = datetime.fromisoformat(published_at)
            published = f"\n🕒 {dt.strftime('%H:%M %d.%m.%Y')}"
        except Exception:
            published = f"\n🕒 {published_at}"
        source = f"\n🌐 {project.get('source', '')}"

        message = f"{title}{url}{description}{skills}{budget}{published}{source}"

        if len(message) > self.MAX_MESSAGE_LENGTH:
            message = message[:self.MAX_MESSAGE_LENGTH] + "…"

        return message
    
    def get_filter_settings_markup(self):
        mode = self.filter_manager.get_filter_mode()
        mode_text = {
            "all": "Усі проєкти",
            "whitelist": "Лише вибрані",
            "blacklist": "Усі, крім вибраних",
        }.get(mode, mode)

        markup = telebot.types.InlineKeyboardMarkup()
        markup.add(telebot.types.InlineKeyboardButton(f"🔄 Режим: {mode_text}", callback_data="toggle_mode"))
        markup.add(telebot.types.InlineKeyboardButton("🛠️ Обрати скіли", callback_data="edit_skills:0"))
        markup.add(telebot.types.InlineKeyboardButton("❌ Вийти", callback_data="delete_message"))

        return markup

    
    def run(self):
        self.bot.polling(none_stop=True)
        