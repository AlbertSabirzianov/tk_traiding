import random

from dotenv import load_dotenv

from app.traiding_view import get_stock_actions
from app.tinkoff_service import TkBroker
from app.settings import TinkoffSettings, StrategySettings, TelegramSettings
from app.schema import StockAction
from app.exceptions import NotFreeCacheForTrading
from app.telegram_mailing import TelegramChanelBot


BUY = "BUY"
SELL = "SELL"

load_dotenv()


def main() -> None:
    """
    Основная функция для автоматизации торговли.

    Функция выполняет следующие шаги:
    1. Загружает настройки из .env файла с помощью `dotenv`.
    2. Инициализирует настройки Тинькофф API и стратегии.
    3. Создаёт экземпляр брокера `TkBroker` для взаимодействия с API.
    4. Проверяет валидность тикеров из настроек стратегии.
    5. Получает рекомендации по торговле (покупка или продажа акций).
    6. Выполняет торговые операции (длинные или короткие позиции) на основе рекомендаций.

    Исключения:
        NotFreeCacheForTrading: Если недостаточно средств для открытия позиции.
    """

    tk_settings = TinkoffSettings()
    strategy_settings = StrategySettings()
    telegram_settings = TelegramSettings()

    tk_broker = TkBroker(
        tok=tk_settings.tk_api_key
    )
    telegram_chanel_bot = TelegramChanelBot(
        bot_token=telegram_settings.bot_token,
        channel_name=telegram_settings.chanel_name
    )

    telegram_chanel_bot.send_message(f"Start trading with {tk_broker.free_money_for_trading}")

    validated_tickers: list[str] = tk_broker.validate_tickers(strategy_settings.stocks)
    stock_actions: list[StockAction] = get_stock_actions(validated_tickers)

    if not stock_actions:
        telegram_chanel_bot.send_message("No recommendations to trading today")
        return
    else:
        telegram_chanel_bot.send_message(f"Stock actions\n {stock_actions}")

    while True:
        current_stock_action: StockAction = random.choice(stock_actions)
        try:
            if current_stock_action.action == BUY:
                tk_broker.post_long_position(
                    ticker=current_stock_action.ticker,
                    take_profit_percent=strategy_settings.profit_percent,
                    stop_loss_percent=strategy_settings.stopp_loss_percent
                )
            elif current_stock_action.action == SELL:
                tk_broker.post_short_position(
                    ticker=current_stock_action.ticker,
                    take_profit_percent=strategy_settings.profit_percent,
                    stop_loss_percent=strategy_settings.stopp_loss_percent
                )
        except NotFreeCacheForTrading:
            telegram_chanel_bot.send_message("Take Positions to all money")
            return
        except Exception as err:
            telegram_chanel_bot.send_message(f"Program finish with error\n {err}")
            return


if __name__ == "__main__":
    main()
