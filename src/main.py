import os
import threading
from dotenv import load_dotenv

from projects_collector.freelancehunt_parser import FreelanceHuntParser
from projects_collector.collector import Collector
from telegram_bot import TelegramBot

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
FREELANCEHUNT_TOKEN = os.getenv("FREELANCEHUNT_TOKEN")

if __name__ == "__main__":
    bot = TelegramBot(TELEGRAM_TOKEN, ADMIN_CHAT_ID)
    fh_parser = FreelanceHuntParser(FREELANCEHUNT_TOKEN)
    collector = Collector([fh_parser], bot.send_projects)

    collector_thread = threading.Thread(target=collector.run, daemon=True)
    bot_thread = threading.Thread(target=bot.run, daemon=True)

    collector_thread.start()
    bot_thread.start()

    collector_thread.join()
    bot_thread.join()