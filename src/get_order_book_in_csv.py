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

    # Проверяем, существует ли файл
    if os.path.exists(filename):
        # Если файл существует, добавляем данные в конец
        data.to_csv(filename, mode='a', header=False, index=False)
    else:
        # Если файл не существует, создаем новый файл с заголовками
        data.to_csv(filename, mode='w', header=True, index=False)


@repeat_trading_with_time_interval_decorator(minutes=1)
def main():
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
            *[f'bid_{num}' for num in range(1, 51)],
            "action"
        ])
        new_row = {
            "price": quotation_to_decimal(order_book.last_price),
            **{f'ask_{num}': order_book.asks[num - 1].quantity for num in range(1, 51)},
            **{f'bid_{num}': order_book.bids[num - 1].quantity for num in range(1, 51)}
        }
        df.loc[0] = new_row
        append_to_csv(data=df, filename=f"{DATA_FOLDER}/{ticker}_{datetime.datetime.now().strftime('%d-%m-%Y')}.csv")


if __name__ == "__main__":
    main()