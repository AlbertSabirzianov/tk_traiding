import datetime
import os
from decimal import Decimal

import pandas as pd
from dotenv import load_dotenv
from tinkoff.invest import Operation, OperationType
from tinkoff.invest.constants import INVEST_GRPC_API
from tinkoff.invest.utils import money_to_decimal

from app.telegram_mailing import TelegramChanelBot
from app.tinkoff_service import get_operations, TkBroker, is_market_open
from app.settings import TinkoffSettings, TelegramSettings, ReportSettings

# Типы операций, относящиеся к комиссиям
COMMISSIONS_TYPES = (
    OperationType.OPERATION_TYPE_TAX,
    OperationType.OPERATION_TYPE_BROKER_FEE,
    OperationType.OPERATION_TYPE_DIVIDEND_TAX,
    OperationType.OPERATION_TYPE_SERVICE_FEE
)

# Типы операций, относящиеся к торговым действиям (покупка/продажа)
ACTIONS_TYPES = (
    OperationType.OPERATION_TYPE_BUY,
    OperationType.OPERATION_TYPE_SELL
)


def append_to_csv(date: str, result_rub: float, result_percent: float, filename: str):
    """
    Добавляет новую строку в CSV файл. Если файл не существует, он будет создан.

    :param date: Дата операции в формате строки (уникальный столбец).
    :param result_rub: Результат торговли в рублях (float).
    :param result_percent: Результат торговли в процентах (float).
    :param filename: Имя CSV файла для записи.
    """
    # Создаем DataFrame с новой строкой
    new_data = pd.DataFrame({
        'date': [date],
        'result_rub': [result_rub],
        'result_percent': [result_percent]
    })

    # Проверяем, существует ли файл
    if os.path.exists(filename):
        # Если файл существует, добавляем данные в конец
        new_data.to_csv(filename, mode='a', header=False, index=False)
    else:
        # Если файл не существует, создаем новый файл с заголовками
        new_data.to_csv(filename, mode='w', header=True, index=False)


def main() -> None:
    """
    Основная функция программы:
    1. Загружает настройки из .env файла.
    2. Получает операции через API Тинькофф Инвестиций.
    3. Рассчитывает результаты торговли.
    4. Отправляет уведомление в Telegram.
    5. Записывает результаты в CSV файл.
    """

    load_dotenv()
    telegram_settings = TelegramSettings()
    tk_settings = TinkoffSettings()
    report_settings = ReportSettings()

    telegram_chanel_bot = TelegramChanelBot(
        bot_token=telegram_settings.bot_token,
        channel_name=telegram_settings.chanel_name
    )
    tk_broker = TkBroker(
        tok=tk_settings.tk_api_key
    )

    operations: list[Operation] = get_operations(
        token=tk_settings.tk_api_key,
        target=INVEST_GRPC_API,
        from_=datetime.datetime.now().replace(hour=0, minute=0, second=0),
        to=datetime.datetime.now()
    ).operations

    commissions: Decimal = Decimal(
        sum(
            [
                money_to_decimal(operation.payment) for operation in filter(
                    lambda x: x.operation_type in COMMISSIONS_TYPES,
                    operations
                )
            ]
        )
    )

    actions_dict: dict[str, dict[OperationType, list[Operation]]] = {}

    for operation in filter(
        lambda x: x.operation_type in ACTIONS_TYPES,
        operations
    ):
        if operation.figi not in actions_dict.keys():
            actions_dict[operation.figi] = {
                OperationType.OPERATION_TYPE_SELL: [],
                OperationType.OPERATION_TYPE_BUY: []
            }
        actions_dict[operation.figi][operation.operation_type].append(operation)

    trading_result: Decimal = Decimal(0)
    for figi in actions_dict.keys():
        while True:
            if (
                not actions_dict[figi][OperationType.OPERATION_TYPE_BUY]
                or not actions_dict[figi][OperationType.OPERATION_TYPE_SELL]
            ):
                break
            trading_result += money_to_decimal(actions_dict[figi][OperationType.OPERATION_TYPE_SELL].pop().payment)
            trading_result += money_to_decimal(actions_dict[figi][OperationType.OPERATION_TYPE_BUY].pop().payment)

    result_percent: Decimal = ((trading_result + commissions) / tk_broker.free_money_for_trading) * Decimal(100)
    icon: str = "🟢" if trading_result + commissions > 0 else "🔴"

    telegram_chanel_bot.send_message(
        f"Trading Result today 📈\n"
        f"{icon}{round(trading_result + commissions, 2)} rub\n"
        f"{icon}{round(result_percent, 2)}%\n"
        f"commissions {round(commissions, 2)}"
    )
    append_to_csv(
        date=datetime.datetime.now().strftime("%d.%m.%Y"),
        result_rub=float(round(trading_result + commissions, 2)),
        result_percent=float(round(result_percent, 2)),
        filename=report_settings.report_file_name
    )


if __name__ == "__main__":
    main()