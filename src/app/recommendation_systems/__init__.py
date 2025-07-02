from .interfaces import ABCRecommendationSystem
from .trading_view_recommendation import TradingViewRecommendationSystem
from .random_recommendation import RandomRecommendationSystem

ALL_RECOMMENDATION_SYSTEMS: dict[str, ABCRecommendationSystem] = {
    "trading_view": TradingViewRecommendationSystem(),
    "random": RandomRecommendationSystem()
}
