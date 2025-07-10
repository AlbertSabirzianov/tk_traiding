import datetime
import os

import pandas as pd
from dotenv import load_dotenv
from tinkoff.invest import GetOrderBookResponse
from tinkoff.invest.utils import quotation_to_decimal

from app.settings import TinkoffSettings, StrategySettings
from app.tinkoff_service import TkBroker
from app.utils import repeat_trading_with_time_interval_decorator


load_dotenv()

DATA_FOLDER = "DATA"


def append_to_csv(data: pd.DataFrame, filename: str):
    """
    Добавляет новую строку в CSV файл. Если файл не существует, он будет создан.

    :param data: Данные для записи
    :param filename: Имя CSV файла для записи.
    """
    if os.path.exists(filename):
        data.to_csv(filename, mode='a', header=False, index=False)
    else:
        data.to_csv(filename, mode='w', header=True, index=False)


@repeat_trading_with_time_interval_decorator(seconds=5)
def main():
    """
    Основная функция для сбора данных о биржевом стакане с использованием API Tinkoff.

    Эта функция выполняет следующие действия:
    1. Инициализирует настройки Tinkoff и стратегии.
    2. Создает экземпляр брокера Tinkoff для взаимодействия с API.
    3. Проверяет и валидирует тикеры акций, указанные в настройках стратегии.
    4. Для каждого валидированного тикера:
        - Получает данные о биржевом стакане.
        - Создает DataFrame для хранения информации о ценах и объемах заявок.
        - Заполняет DataFrame данными о последней цене, объемах заявок на покупку и продажу.
        - Сохраняет данные в CSV файл с именем, основанным на тикере и текущей дате.

    Декоратор `repeat_trading_with_time_interval_decorator` обеспечивает выполнение этой функции
     с заданным интервалом времени (в данном случае, каждые 1 минуту).

    Возвращаемое значение:
        None
    """
    tk_settings = TinkoffSettings()
    strategy_settings = StrategySettings()

    tk_broker = TkBroker(
        tok=tk_settings.tk_api_key
    )
    validated_tickers: list[str] = tk_broker.validate_tickers(strategy_settings.stocks)

    for ticker in validated_tickers:
        order_book:  GetOrderBookResponse = tk_broker.get_order_book_by_ticker(ticker)
        df = pd.DataFrame(columns=[
            "price",
            *[f'ask_{num}' for num in range(1, 51)],
            *[f'bid_{num}' for num in range(1, 51)]
        ])
        new_row = {
            "price": quotation_to_decimal(order_book.last_price),
            **{f'ask_{num + 1}': asc.quantity for num, asc in enumerate(order_book.asks)},
            **{f'bid_{num + 1}': bid.quantity for num, bid in enumerate(order_book.bids)}
        }
        df.loc[0] = new_row
        append_to_csv(data=df, filename=f"{DATA_FOLDER}/{ticker}_{datetime.datetime.now().strftime('%d-%m-%Y')}.csv")


if __name__ == "__main__":
    main()