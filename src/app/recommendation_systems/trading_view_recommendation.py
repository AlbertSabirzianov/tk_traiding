from tradingview_ta import TA_Handler, Recommendation

from ..schema import StockAction
from ..settings import TradingViewSettings
from ..utils import connection_problems_decorator
from .interfaces import ABCRecommendationSystem

tradingview_settings = TradingViewSettings()


@connection_problems_decorator
def get_stock_summary(stock: str) -> dict:
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
        interval='1d'
    )
    return handler.get_analysis().summary


class TradingViewRecommendationSystem(ABCRecommendationSystem):
    """
     Система рекомендаций, которая генерирует действия для торговли акциями
     на основе анализа TradingView.

     Методы:
         get_stock_actions(stocks: list[str]) -> list[StockAction]:
             Генерирует список экземпляров StockAction для заданных акций,
             случайным образом присваивая каждой акции действие BUY или SELL.

     Параметры:
         stocks (list[str]): Список тикеров акций, для которых необходимо
                             сгенерировать рекомендации.

     Возвращает:
         list[StockAction]: Список объектов StockAction, содержащих тикер
                            акции и случайно выбранное действие (BUY или SELL).
     """

    def get_stock_actions(self, stocks: list[str]) -> list[StockAction]:
        """
        Определяет действия (покупка или продажа) для списка акций на основе анализа TradingView.

        Args:
            stocks (list[str]): Список тикеров акций.

        Returns:
            list[StockAction]: Список объектов StockAction с рекомендациями для каждой акции.
        """
        stock_actions = []
        for ticker in stocks:
            summary = get_stock_summary(ticker)
            if summary["RECOMMENDATION"] in (Recommendation.neutral, Recommendation.error):
                print(f"Stock {ticker} not recommend to trading today")
                continue
            if summary["RECOMMENDATION"] in (Recommendation.buy, Recommendation.strong_buy):
                stock_actions.append(
                    StockAction(
                        ticker=ticker,
                        action=Recommendation.buy
                    )
                )
            elif summary["RECOMMENDATION"] in (Recommendation.sell, Recommendation.strong_sell):
                stock_actions.append(
                    StockAction(
                        ticker=ticker,
                        action=Recommendation.sell
                    )
                )
        return stock_actions


