from tinkoff.invest import CandleInterval

from .interfaces import ABCRecommendationSystem
from .trading_view_recommendation import TradingViewRecommendationSystem
from .random_recommendation import RandomRecommendationSystem
from .rsi_recommendation import RSIRecommendationSystem
from .stochastic_rsi_recommendation import StochasticRSIRecommendationSystem
from .only_by_trend_recommendation import OnlyByTrendRecommendationSystem
from .moving_average_recommendation_system import MovingAverageRecommendationSystem
from .logistic_model_recommendation_system import LogisticModelRecommendationSystem

ALL_RECOMMENDATION_SYSTEMS: dict[str, ABCRecommendationSystem] = {
    "logistic_model": LogisticModelRecommendationSystem(),
    "trading_view": TradingViewRecommendationSystem(),
    "random": RandomRecommendationSystem(),
    "rsi": RSIRecommendationSystem(),
    "stoch_rsi": StochasticRSIRecommendationSystem(),
    "rsi_only_by_trend": OnlyByTrendRecommendationSystem(
        recommendation_system=RSIRecommendationSystem()
    ),
    "stoch_rsi_only_by_trend": OnlyByTrendRecommendationSystem(
        recommendation_system=StochasticRSIRecommendationSystem()
    ),
    "moving_average": MovingAverageRecommendationSystem(),
    "moving_average_5_min": MovingAverageRecommendationSystem(candle_interval=CandleInterval.CANDLE_INTERVAL_5_MIN),
    "moving_average_5_min_only_by_trend": OnlyByTrendRecommendationSystem(
        recommendation_system=MovingAverageRecommendationSystem(
            candle_interval=CandleInterval.CANDLE_INTERVAL_5_MIN
        ),
        candle_interval=CandleInterval.CANDLE_INTERVAL_5_MIN,
    )
}
