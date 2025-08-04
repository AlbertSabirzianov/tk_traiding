from .interfaces import ABCRecommendationSystem
from ..schema import StockAction
from ..contains import BUY, SELL, UPTREND, DOWNTREND
from ..settings import TinkoffSettings
from ..tinkoff_service import TkBroker


class OnlyByTrendRecommendationSystem(ABCRecommendationSystem):

    def __init__(self, recommendation_system: ABCRecommendationSystem):
        self.recommendation_system = recommendation_system

    def get_stock_actions(self, stocks: list[str]) -> list[StockAction]:
        stock_actions: list[StockAction] = self.recommendation_system.get_stock_actions(stocks)
        only_by_trend_actions: list[StockAction] = []

        tk_settings = TinkoffSettings()
        tk_broker = TkBroker(
            tok=tk_settings.tk_api_key
        )

        for stock_action in stock_actions:
            trend = tk_broker.get_trend_by_ticker(stock_action.ticker)
            if trend == DOWNTREND and stock_action.action == SELL:
                only_by_trend_actions.append(stock_action)
            elif trend == UPTREND and stock_action.action == BUY:
                only_by_trend_actions.append(stock_action)
        return only_by_trend_actions