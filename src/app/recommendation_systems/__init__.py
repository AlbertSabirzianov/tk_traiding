from .interfaces import ABCRecommendationSystem
from .trading_view_recommendation import TradingViewRecommendationSystem
from .random_recommendation import RandomRecommendationSystem
from .rsi_recommendation import RSIRecommendationSystem
from .stochastic_rsi_recommendation import StochasticRSIRecommendationSystem

ALL_RECOMMENDATION_SYSTEMS: dict[str, ABCRecommendationSystem] = {
    "trading_view": TradingViewRecommendationSystem(),
    "random": RandomRecommendationSystem(),
    "rsi": RSIRecommendationSystem(),
    "stoch_rsi": StochasticRSIRecommendationSystem(),
}
