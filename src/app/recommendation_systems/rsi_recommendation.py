from tradingview_ta import TA_Handler, Analysis, Interval

from ..contains import SELL, BUY
from ..schema import StockAction
from ..settings import TradingViewSettings
from ..utils import connection_problems_decorator
from .interfaces import ABCRecommendationSystem

tradingview_settings = TradingViewSettings()


@connection_problems_decorator
def get_stock_analysis(stock: str) -> Analysis:
    """
    Получает сводный анализ по акции с использованием TradingView_TA.

    Args:
        stock (str): Тикер акции.

    Returns:
        dict: Сводный анализ, содержащий рекомендации и другие данные.
    """
    handler = TA_Handler(
        symbol=stock,
        exchange=tradingview_settings.exchange,
        screener=tradingview_settings.screener,
        interval=Interval.INTERVAL_15_MINUTES
    )
    return handler.get_analysis()


class RSIRecommendationSystem(ABCRecommendationSystem):
    """
    Класс системы рекомендаций на основе индикатора RSI (Relative Strength Index).

    Для каждого тикера из переданного списка получает анализ с техническими индикаторами,
    после чего формирует торговые рекомендации:
    - Если RSI выше 70, считается, что акция перекуплена, и генерируется сигнал на продажу (SELL).
    - Если RSI ниже 30, считается, что акция перепродана, и генерируется сигнал на покупку (BUY).

    Методы:
    --------
    get_stock_actions(stocks: list[str]) -> list[StockAction]
        Принимает список тикеров акций и возвращает список торговых действий (покупка или продажа)
        на основе значений RSI для каждой акции.
    """
    def get_stock_actions(self, stocks: list[str]) -> list[StockAction]:
        stock_actions: list[StockAction] = []

        for ticker in stocks:
            analysis: Analysis = get_stock_analysis(stock=ticker)
            if analysis.indicators["RSI"] > 70:
                stock_actions.append(
                    StockAction(
                        ticker=ticker,
                        action=SELL
                    )
                )
            if analysis.indicators["RSI"] < 30:
                stock_actions.append(
                    StockAction(
                        ticker=ticker,
                        action=BUY
                    )
                )

        return stock_actions
