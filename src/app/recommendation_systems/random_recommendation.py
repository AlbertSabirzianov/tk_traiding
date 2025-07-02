import random

from .interfaces import ABCRecommendationSystem
from ..schema import StockAction
from ..contains import BUY, SELL


class RandomRecommendationSystem(ABCRecommendationSystem):
    """
     Система рекомендаций, которая генерирует случайные действия для торговли акциями.

     Этот класс наследует ABCRecommendationSystem и реализует метод,
     который предоставляет рекомендации по торговле акциями на основе
     случайного выбора. Для каждой акции из предоставленного списка
     случайным образом определяется, рекомендовать ли купить или продать
     акцию.

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
        actions: list[StockAction] = []
        for stock in stocks:
            actions.append(
                StockAction(
                   ticker=stock,
                   action=random.choice((BUY, SELL))
                )
            )
        return actions
