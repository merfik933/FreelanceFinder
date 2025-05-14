import telebot
from datetime import datetime

class TelegramBot:
    def __init__(self, token, admin_id):
        self.bot = telebot.TeleBot(token)
        self.token = token
        self.admin_id = admin_id

        self.MAX_MESSAGE_LENGTH = 4096
        self.MAX_DESCRIPTION_LENGTH = 2048
        
        self._register_handlers()

    def _register_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def start(message):
            self.bot.send_message(message.chat.id, "Welcome to the bot!")

        @self.bot.message_handler(commands=['id'])
        def send_id(message):
            self.bot.send_message(message.chat.id, f"Your ID: {message.chat.id}")    

    def send_projects(self, project):
        message = self.format_project_message(project)
        self.bot.send_message(self.admin_id, message, parse_mode='HTML', disable_web_page_preview=True)
        
    def format_project_message(self, project: dict) -> str:
        title = f"<b>{project['title']}</b>"
        url = f"\n🔗{project['url']}"
        description = project.get('description') or ""
        if len(description) > self.MAX_DESCRIPTION_LENGTH:
            description = description[:self.MAX_DESCRIPTION_LENGTH] + "…"
        description = f"\n\n{description}"
        skills = f"\n\n🛠️ Навички: {', '.join(project.get('skills', []))}" if project.get('skills') else ""
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
    
    def run(self):
        self.bot.polling(none_stop=True)
        