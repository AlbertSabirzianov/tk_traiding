from abc import ABC, abstractmethod

from ..schema import StockAction


class ABCRecommendationSystem(ABC):

    @abstractmethod
    def get_stock_actions(self, stocks: list[str]) -> list[StockAction]:
        raise NotImplementedError
