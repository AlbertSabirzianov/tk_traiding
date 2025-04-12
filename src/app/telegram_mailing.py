import asyncio

from telegram import Bot


def send_message_to_telegram(bot_token: str, channel_name: str, message: str):
    bot = Bot(token=bot_token)
    asyncio.run(bot.send_message(chat_id=channel_name, text=message))
