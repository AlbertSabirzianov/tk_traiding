"""
Этот модуль определяет абстрактный базовый класс
для системы рекомендаций, которая предоставляет действия с акциями на основе списка акций.

Классы:
    ABCRecommendationSystem (ABC): Абстрактный базовый класс, который описывает структуру
    для любой системы рекомендаций по акциям.

Методы:
    get_stock_actions(stocks: list[str]) -> list[StockAction]:
        Абстрактный метод, который должен быть реализован в любом подклассе.
        Он принимает список символов акций в качестве входных данных и возвращает список объектов StockAction,
         представляющих рекомендуемые действия для указанных акций.

Использование:
    Чтобы создать конкретную реализацию системы рекомендаций по акциям,
     создайте подкласс ABCRecommendationSystem и реализуйте метод get_stock_actions.
"""
from abc import ABC, abstractmethod

from ..schema import StockAction


class ABCRecommendationSystem(ABC):

    @abstractmethod
    def get_stock_actions(self, stocks: list[str]) -> list[StockAction]:
        raise NotImplementedError
