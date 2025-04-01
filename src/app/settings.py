from pydantic_settings import BaseSettings


class TradingViewSettings(BaseSettings):
    exchange: str = "RUS"
    screener: str = "russia"


class StrategySettings(BaseSettings):
    profit_percent: float
    stopp_loss_percent: float
    stocks: list[str]


class TinkoffSettings(BaseSettings):
    tk_api_key: str

