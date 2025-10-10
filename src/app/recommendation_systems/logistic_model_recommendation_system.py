import joblib
import datetime

import pandas as pd
from ta import add_all_ta_features
from tinkoff.invest import CandleInterval

from .interfaces import ABCRecommendationSystem
from ..schema import StockAction
from ..settings import TinkoffSettings
from ..tinkoff_service import TkBroker
from ..contains import *


class LogisticModelRecommendationSystem(ABCRecommendationSystem):
    """
    Класс LogisticModelRecommendationSystem реализует систему рекомендаций для торговли акциями
    на основе логистической регрессии.

    Основные возможности:
    - Подготовка данных с использованием технических индикаторов (через функцию add_all_ta_features).
    - Загрузка предварительно обученных моделей и масштабаторов для каждого тикера.
    - Получение последних данных по свечам за последние сутки с заданным интервалом.
    - Прогнозирование действия (покупка или продажа) на основе логистической регрессии.
    - Формирование списка рекомендаций по акциям в виде объектов StockAction.

    Атрибуты:
        candle_interval (CandleInterval): Интервал свечей для анализа (по умолчанию 5 минут).

    Методы:
        prepare_data(df: pd.DataFrame) -> pd.DataFrame:
            Статический метод для подготовки и обогащения исходных данных техническими индикаторами,
            удаления ненужных столбцов и пропусков.

        get_stock_actions(stocks: list[str]) -> list[StockAction]:
            Для каждого тикера из списка загружает модель и масштабатор, получает данные по свечам,
            подготавливает данные, делает прогноз и формирует рекомендации по покупке или продаже.
    """

    def __init__(self, candle_interval=CandleInterval.CANDLE_INTERVAL_5_MIN):
        self.candle_interval=candle_interval

    @staticmethod
    def prepare_data(df: pd.DataFrame) -> pd.DataFrame:
        all_df = add_all_ta_features(
            df,
            open="open",  # noqa
            high="high",
            low="low",
            close="close",
            volume="volume"
        )

        all_df = all_df.drop("trend_psar_up", axis=1)
        all_df = all_df.drop("trend_psar_down", axis=1)
        all_df = all_df.dropna()
        return all_df.drop("time", axis=1)

    def get_stock_actions(self, stocks: list[str]) -> list[StockAction]:
        stock_actions: list[StockAction] = []

        for ticker in stocks:
            scaler = joblib.load(f"DATA/{ticker}_logistic_scaler.pkl")
            model = joblib.load(f"DATA/{ticker}_logistic_model.pkl")
            poly = joblib.load(f"DATA/{ticker}_logistic_poly.pkl")

            tk_broker = TkBroker(tok=TinkoffSettings().tk_api_key)
            df = tk_broker.get_candles_from_ticker(
                ticker=ticker,
                from_=datetime.datetime.now() - datetime.timedelta(days=1),
                to_=datetime.datetime.now(),
                candl_interval=self.candle_interval
            )

            all_df = self.prepare_data(df)
            predict = model.predict(scaler.transform(poly.transform(all_df)))

            if predict[-1] == BUY:
                stock_actions.append(
                    StockAction(
                        ticker=ticker,
                        action=BUY
                    )
                )
            if predict[-1] == SELL:
                stock_actions.append(
                    StockAction(
                        ticker=ticker,
                        action=SELL
                    )
                )
        return stock_actions
