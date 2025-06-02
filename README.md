# FreelanceFinder

FreelanceFinder is a service that quickly notifies users about new projects from various freelance platforms, with filtering and other useful features.

## Key features

- Available via Telegram Bot
- Project filtering to avoid irrelevant notifications.

## Dependencies

All dependencies are specified in the `requirements.txt` file.

## Environment Variables

To ensure correct operation, the following environment variables must be set:

* `FREELANCEHUNT_TOKEN` – Token for accessing the FreelanceHunt API.
  Instructions on how to obtain it can be found in the official documentation: `https://apidocs.freelancehunt.com`
* `TELEGRAM_TOKEN` – Token used to access the Telegram Bot API.
  You must create a new bot via [BotFather](https://t.me/BotFather), the official Telegram bot for creating and managing bots, to obtain this token.
* `ADMIN_CHAT_ID` - Admin chat id.
  To get your chat id, you can start the bot and enter the /id command
