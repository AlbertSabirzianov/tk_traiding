import asyncio

from telegram import Bot


def send_message_to_telegram(bot_token: str, channel_name: str, message: str):
    """
    Отправляет сообщение в указанный канал Telegram.

    Аргументы:
        bot_token (str): Токен бота Telegram.
        channel_name (str): Имя канала (или chat_id), куда будет отправлено сообщение.
        message (str): Сообщение, которое нужно отправить.
    """
    bot = Bot(token=bot_token)
    asyncio.run(bot.send_message(chat_id=channel_name, text=message))


class TelegramChanelBot:
    """
    Класс для работы с ботом Telegram, который отправляет сообщения в канал.

    Аргументы:
        bot_token (str): Токен бота Telegram.
        channel_name (str): Имя канала (или chat_id), куда будут отправляться сообщения.
    """
    def __init__(self, bot_token: str, channel_name: str):
        self.bot_token = bot_token
        self.channel_name = channel_name

    def send_message(self, message: str):
        """
        Отправляет сообщение в указанный канал Telegram.

        Аргументы:
            message (str): Сообщение, которое нужно отправить.
        """
        send_message_to_telegram(
            bot_token=self.bot_token,
            channel_name=self.channel_name,
            message=message
        )