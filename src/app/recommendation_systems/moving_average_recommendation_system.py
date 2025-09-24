import pandas
from tinkoff.invest import CandleInterval

from .interfaces import ABCRecommendationSystem
from ..schema import StockAction
from ..tinkoff_service import TkBroker
from ..settings import TinkoffSettings
from ..contains import BUY, SELL


class MovingAverageRecommendationSystem(ABCRecommendationSystem):
    """
    Система рекомендаций для торговли акциями на основе пересечений скользящих средних (EMA).

    Использует данные экспоненциальных скользящих средних с двумя периодами (коротким и длинным),
    получаемые через брокерский API Tinkoff. Для каждого тикера из списка анализирует последние значения EMA
    и генерирует торговые сигналы:
      - Покупка (BUY), если короткая EMA пересекает длинную EMA снизу вверх.
      - Продажа (SELL), если короткая EMA пересекает длинную EMA сверху вниз.

    Атрибуты:
        candle_interval (CandleInterval): интервал свечей для расчёта EMA (по умолчанию 15 минут).

    Методы:
        get_stock_actions(stocks: list[str]) -> list[StockAction]:
            Принимает список тикеров, возвращает список торговых действий на основе анализа EMA.
    """

    def __init__(self, candle_interval: CandleInterval = CandleInterval.CANDLE_INTERVAL_15_MIN):
        self.candle_interval = candle_interval

    def get_stock_actions(self, stocks: list[str]) -> list[StockAction]:
        tinkoff_settings = TinkoffSettings()
        tk_broker = TkBroker(tok=tinkoff_settings.tk_api_key)

        stock_actions: list[StockAction] = []
        for stock in stocks:
            ema_data: pandas.DataFrame = tk_broker.get_ema_by_ticker(
                ticker=stock,
                candle_interval=self.candle_interval
            )
            ema_short = ema_data["ema_short"]
            ema_long = ema_data["ema_long"]

            if ema_short.iloc[-1] > ema_long.iloc[-1] and ema_short.iloc[-2] <= ema_long.iloc[-2]:
                stock_actions.append(
                    StockAction(
                        ticker=stock,
                        action=BUY
                    )
                )
            if ema_short.iloc[-1] < ema_long.iloc[-1] and ema_short.iloc[-2] >= ema_long.iloc[-2]:
                stock_actions.append(
                    StockAction(
                        ticker=stock,
                        action=SELL
                    )
                )
        return stock_actions
