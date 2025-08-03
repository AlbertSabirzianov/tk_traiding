from dotenv import load_dotenv
from pandas import DataFrame

from .interfaces import ABCRecommendationSystem
from ..schema import StockAction
from ..settings import TinkoffSettings
from ..tinkoff_service import TkBroker

load_dotenv()

class StochasticRSIRecommendationSystem(ABCRecommendationSystem):
    """
    Торговая система, основанная на стратегии с использованием индикатора Stochastic RSI.

    Стратегия анализирует значения %K и %D Stochastic RSI
    для набора акций и генерирует торговые сигналы "BUY" или "SELL"
    на основе классического пересечения линий индикатора в зонах перепроданности и перекупленности.

    Логика работы:
    - Для каждой акции вычисляются значения Stochastic RSI (%K и %D) на исторических данных.
    - Сравниваются значения %K и %D на двух последних точках времени: предыдущем и текущем.
    - Сигнал на покупку ("BUY") возникает, если:
        * В предыдущий момент %K была ниже %D (k_prev < d_prev),
        * В текущий момент %K пересекла %D снизу вверх (k_curr > d_curr),
        * При этом текущее значение %K находится в зоне перепроданности (k_curr < 0.2).
          Это указывает на возможный разворот цены вверх из перепроданной зоны.

    - Сигнал на продажу ("SELL") возникает, если:
        * В предыдущий момент %K была выше %D (k_prev > d_prev),
        * В текущий момент %K пересекла %D сверху вниз (k_curr < d_curr),
        * При этом текущее значение %K находится в зоне перекупленности (k_curr > 0.8).
          Это указывает на возможный разворот цены вниз из перекупленной зоны.

    Таким образом, стратегия использует классические сигналы стохастического осциллятора, применённого к RSI,
    для определения моментов входа и выхода из позиций, ориентируясь на зоны экстремальных значений индикатора.

    Возвращаемое значение:
    - Список объектов StockAction с тикером и рекомендованным действием ("BUY" или "SELL") для каждой акции,
     удовлетворяющей условиям стратегии.

    Примечание:
    - Для повышения надёжности сигналов рекомендуется использовать дополнительные фильтры и учитывать общий тренд рынка.
    """

    def get_stock_actions(self, stocks: list[str]) -> list[StockAction]:


        tk_settings = TinkoffSettings()
        tk_broker = TkBroker(
            tok=tk_settings.tk_api_key
        )

        stock_actions: list[StockAction] = []

        for ticker in stocks:
            stochastic_rsi_df: DataFrame = tk_broker.get_stochastic_rsi_by_ticker(ticker)

            k_prev = stochastic_rsi_df['stoch_rsi_k'].iloc[-2]
            d_prev = stochastic_rsi_df['stoch_rsi_d'].iloc[-2]
            k_curr = stochastic_rsi_df['stoch_rsi_k'].iloc[-1]
            d_curr = stochastic_rsi_df['stoch_rsi_d'].iloc[-1]

            if (k_prev < d_prev) and (k_curr > d_curr) and (k_curr < 0.2):
                stock_actions.append(
                    StockAction(
                        ticker=ticker,
                        action="BUY"
                    )
                )

            elif (k_prev > d_prev) and (k_curr < d_curr) and (k_curr > 0.8):
                stock_actions.append(
                    StockAction(
                        ticker=ticker,
                        action="SELL"
                    )
                )
        return stock_actions