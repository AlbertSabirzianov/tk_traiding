import pandas as pd


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