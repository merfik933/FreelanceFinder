import os
import threading
from dotenv import load_dotenv

from projects_collector.freelancehunt_parser import FreelanceHuntParser
from projects_collector.collector import Collector
from telegram_bot.bot import TelegramBot

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID"))
FREELANCEHUNT_TOKEN = os.getenv("FREELANCEHUNT_TOKEN")

assert TELEGRAM_TOKEN, "Missing TELEGRAM_TOKEN in .env"
assert ADMIN_CHAT_ID, "Missing ADMIN_CHAT_ID in .env"
assert FREELANCEHUNT_TOKEN, "Missing FREELANCEHUNT_TOKEN in .env"

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