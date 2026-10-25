# FreelanceFinder

FreelanceFinder is a service that quickly notifies users about new projects from various freelance platforms, with filtering and other useful features.

⚠️ This is a protected project. The code is published for portfolio and educational purposes only.
Any usage, reproduction, or modification without explicit permission from the author is prohibited.
For inquiries or collaboration, contact anatoliy9370@gmail.com.

## Key features

- Available via Telegram Bot
- Project filtering to avoid irrelevant notifications.
- On startup, catches up on projects newer than the saved ID, up to three days old, using API pagination. Existing filters apply; the ID is saved after each successfully processed project. The first run also covers the last three days. Only projects still returned by the API can be recovered.

## Dependencies

All dependencies are specified in the `requirements.txt` file.

## Environment Variables

To ensure correct operation, the following environment variables must be set:

* `FREELANCEHUNT_TOKEN` – Token for accessing the FreelanceHunt API.
  Instructions on how to obtain it can be found in the official documentation: `https://apidocs.freelancehunt.com`
* `TELEGRAM_TOKEN` – Token used to access the Telegram Bot API.
  You must create a new bot via [BotFather](https://t.me/BotFather), the official Telegram bot for creating and managing bots, to obtain this token.
  <<<<<<< HEAD
* `ADMIN_CHAT_ID` – id of the admin's chat with the bot.id чат админа с ботом
  To obtain, use the command /id
  =======

License: This project is proprietary. See LICENSE for details.
