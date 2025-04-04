import random

from dotenv import load_dotenv

from app.traiding_view import get_stock_actions
from app.tinkoff_service import TkBroker
from app.settings import TinkoffSettings, StrategySettings
from app.schema import StockAction
from app.exceptions import NotFreeCacheForTrading


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

    tk_broker = TkBroker(
        tok=tk_settings.tk_api_key
    )
    validated_tickers: list[str] = tk_broker.validate_tickers(strategy_settings.stocks)
    stock_actions: list[StockAction] = get_stock_actions(validated_tickers)

    if not stock_actions:
        print("No recommendations to trading today")
        return

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
            print("Take Positions to all money")
            return


if __name__ == "__main__":
    main()
