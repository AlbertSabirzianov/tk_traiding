from decimal import Decimal
from typing import Union

from dotenv import load_dotenv

from .interfaces import ABCRecommendationSystem
from ..contains import SELL, BUY
from ..schema import StockAction
from ..settings import TinkoffSettings
from ..tinkoff_service import TkBroker

load_dotenv()


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

        tk_settings = TinkoffSettings()
        tk_broker = TkBroker(
            tok=tk_settings.tk_api_key
        )

        stock_actions: list[StockAction] = []

        for ticker in stocks:
            rsi: Union[Decimal, float] = tk_broker.get_rsi_by_ticker(ticker)
            if rsi > 70:
                stock_actions.append(
                    StockAction(
                        ticker=ticker,
                        action=SELL
                    )
                )
            if rsi < 30:
                stock_actions.append(
                    StockAction(
                        ticker=ticker,
                        action=BUY
                    )
                )

        return stock_actions
