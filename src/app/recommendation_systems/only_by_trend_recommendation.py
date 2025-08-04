from .interfaces import ABCRecommendationSystem
from ..schema import StockAction
from ..contains import BUY, SELL, UPTREND, DOWNTREND
from ..settings import TinkoffSettings
from ..tinkoff_service import TkBroker


class OnlyByTrendRecommendationSystem(ABCRecommendationSystem):
    """
    Обёртка для другого рекомендательного сервиса, которая фильтрует торговые сигналы
    по направлению текущего тренда инструмента.

    Данный класс принимает в конструкторе другой объект, реализующий интерфейс ABCRecommendationSystem,
    и вызывает его метод get_stock_actions для получения первоначальных рекомендаций.

    После этого для каждой рекомендации определяется текущий тренд инструмента с помощью метода
    get_trend_by_ticker из TkBroker.

    Логика фильтрации:
    - Если тренд нисходящий (DOWNTREND), то оставляются только сигналы на продажу (SELL).
    - Если тренд восходящий (UPTREND), то оставляются только сигналы на покупку (BUY).
    - Все остальные сигналы отбрасываются.

    Таким образом, стратегия ограничивает торговлю только теми действиями, которые соответствуют
    направлению тренда, что помогает снизить количество ложных сигналов и повысить качество рекомендаций.

    Возвращаемое значение:
    - Список объектов StockAction, отфильтрованных по тренду.

    Пример использования:
        base_system = SomeRecommendationSystem()
        filtered_system = OnlyByTrendRecommendationSystem(base_system)
        actions = filtered_system.get_stock_actions(['AAPL', 'TSLA', 'GOOG'])
    """

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