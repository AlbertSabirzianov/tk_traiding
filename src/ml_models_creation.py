import datetime

import pandas as pd
from ta import add_all_ta_features
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
import joblib
from tinkoff.invest import CandleInterval

from app.tinkoff_service import TkBroker
from app.settings import TinkoffSettings, StrategySettings



def get_actions(stop_loss_percent: float, take_profit_percent: float, prices: pd.Series) -> pd.Series:
    """
    Определяет торговые действия ("BUY", "SELL", "NOTHING")
    для каждой цены в серии на основе заданных уровней стоп-лосса и тейк-профита.

    Для каждой цены из входной серии функция анализирует будущие цены и принимает решение:

    - "BUY" — если в будущем цена вырастет минимум на take_profit_percent %,
       при этом не опустится ниже уровня стоп-лосса (stop_loss_percent % снижения).

    - "SELL" — если в будущем цена упадет минимум на take_profit_percent %,
     при этом не поднимется выше уровня стоп-лосса (stop_loss_percent % роста).

    - "NOTHING" — если ни одно из условий не выполнено.

    Параметры:
    stop_loss_percent (float): Процент стоп-лосса (например, 0.3 для 0.3%).
    take_profit_percent (float): Процент тейк-профита (например, 1.0 для 1%).
    prices (pd.Series): Серия с ценами акций, индекс которой отражает временной порядок.

    Возвращает:
    pd.Series: Серия с теми же индексами,
    что и входная, содержащая строки "BUY", "SELL" или "NOTHING" для каждой цены.
    """
    actions = []
    for index, price in prices.items():
        take_profit_byu: float = price + price * (take_profit_percent/100)
        take_profit_sell: float = price - price * (take_profit_percent/100)
        stop_loss_byu: float = price - price * (stop_loss_percent/100)
        stop_loss_sell: float = price + price * (stop_loss_percent/100)

        future_prices: pd.Series = prices[index:]

        take_profit_byu_prices = future_prices[future_prices >= take_profit_byu]
        take_profit_sell_prices = future_prices[future_prices <= take_profit_sell]
        stop_loss_byu_prices = future_prices[future_prices <= stop_loss_byu]
        stop_loss_sell_prices = future_prices[future_prices >= stop_loss_sell]

        if not take_profit_byu_prices.empty:
            if stop_loss_byu_prices.empty or stop_loss_byu_prices.index[0] > take_profit_byu_prices.index[0]:
                actions.append("BUY")
                continue
        if not take_profit_sell_prices.empty:
            if stop_loss_sell_prices.empty or stop_loss_sell_prices.index[0] > take_profit_sell_prices.index[0]:
                actions.append("SELL")
                continue
        actions.append("NOTHING")
    return pd.Series(actions, index=prices.index.to_list())


def get_workday_time_ranges_last_days(days: int) -> list[tuple[datetime.datetime, datetime.datetime]]:
    """
    Возвращает список кортежей с временными интервалами (с 7:00 утра до 23:00 вечера)
    для всех рабочих дней за последние заданное количество дней, включая сегодняшний день.

    Рабочими днями считаются дни недели с понедельника по пятницу (weekday 0-4).

    Параметры:
    ----------
    days : int
        Количество последних дней (включая сегодняшний), за которые нужно получить интервалы.
        Например, если days=10, функция вернёт интервалы для рабочих дней за последние 10 дней.

    Возвращаемое значение:
    ----------------------
    list of tuples
        Список кортежей вида (datetime_7am, datetime_11pm), где:
        - datetime_7am — объект datetime, соответствующий 7:00 утра рабочего дня,
        - datetime_11pm — объект datetime, соответствующий 23:00 вечера того же рабочего дня.

    Особенности работы:
    -------------------
    - Функция использует текущую дату и время системы (datetime.today()).
    - Интервалы формируются для каждого рабочего дня в диапазоне от (сегодня - days) до сегодня включительно.
    - Если день приходится на выходной (суббота или воскресенье), он пропускается.
    - Временные метки создаются на основе даты дня и фиксированного времени (7:00 и 23:00).
    """
    from datetime import datetime, timedelta, time

    today = datetime.today()
    first_day = today - timedelta(days=days)

    result = []
    current_day = first_day

    while current_day <= today:
        if current_day.weekday() < 5:
            dt_7am = datetime.combine(current_day.date(), time(7, 0))
            dt_11pm = datetime.combine(current_day.date(), time(23, 0))
            result.append((dt_7am, dt_11pm))
        current_day += timedelta(days=1)

    return result


def create_and_write_logistic_model_to_file(
    ticker: str,
    days: int,
    data_folder: str,
) -> None:
    """
    Создаёт и сохраняет модель логистической регрессии для заданного инструмента (тикера)
    на основе исторических 5-минутных свечей.

    Функция выполняет следующие шаги:
    1. Проверяет валидность тикера через брокерский API.
    2. Загружает данные по свечам за последние `days` рабочих дней с интервалом 5 минут.
    3. Объединяет полученные данные в один DataFrame.
    4. Добавляет технические индикаторы с помощью библиотеки `ta`.
    5. Удаляет некоторые колонки и пропуски.
    6. Рассчитывает целевую переменную "action" с помощью функции `get_actions`.
    7. Стандартизирует признаки с помощью `StandardScaler` и сохраняет объект scaler в файл.
    8. Обучает модель логистической регрессии на стандартизированных данных и сохраняет модель в файл.

    Параметры:
    -----------
    ticker : str
        Тикер инструмента (акции), для которого создаётся модель.
    days : int
        Количество последних рабочих дней, за которые загружаются данные.
    data_folder : str
        Путь к папке, в которую будут сохранены файлы scaler и модели.

    Возвращаемое значение:
    ----------------------
    None
        Функция сохраняет обученные объекты scaler и модели в файлы и не возвращает значение.

    Исключения:
    -----------
    Если тикер невалиден, функция завершает работу без создания модели.
    """
    tk_broker = TkBroker(tok=TinkoffSettings().tk_api_key)
    if not tk_broker.validate_tickers(stock_tickers=[ticker]):
        return

    dfs = []
    for start_day, end_day in get_workday_time_ranges_last_days(days=days):
        dfs.append(
            tk_broker.get_candles_from_ticker(
                ticker=ticker,
                from_=start_day,
                to_=end_day,
                candl_interval=CandleInterval.CANDLE_INTERVAL_5_MIN
            )
        )
    df = pd.concat(dfs)

    all_df = add_all_ta_features(
        df,
        open="open",  # noqa
        high="high",
        low="low",
        close="close",
        volume="volume"
    )

    all_df = all_df.drop("trend_psar_up", axis=1)
    all_df = all_df.drop("trend_psar_down", axis=1)
    all_df = all_df.dropna()

    all_df["action"] = get_actions(
        stop_loss_percent=StrategySettings().stopp_loss_percent,
        take_profit_percent=StrategySettings().profit_percent,
        prices=all_df["close"]
    )
    all_df = all_df.drop("time", axis=1)

    scaler = StandardScaler()
    scaler.fit(all_df.drop("action", axis=1))
    joblib.dump(scaler, f"{data_folder}/{ticker}_logistic_scaler.pkl")

    model = LogisticRegression(max_iter=1000)
    model.fit(scaler.transform(all_df.drop("action", axis=1)), all_df["action"])
    joblib.dump(model, f"{data_folder}/{ticker}_logistic_model.pkl")


if __name__ == "__main__":
    from dotenv import load_dotenv
    load_dotenv()

    strategy_settings = StrategySettings()

    for ticker in strategy_settings.stocks:
        create_and_write_logistic_model_to_file(
            ticker=ticker,
            days=30,
            data_folder="DATA"
        )
