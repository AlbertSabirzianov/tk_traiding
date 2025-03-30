from tradingview_ta import TA_Handler, Recommendation

from .schema import StockAction
from .settings import TradingViewSettings


tradingview_settings = TradingViewSettings()


def __get_stock_summary(stock: str) -> dict:
    handler = TA_Handler(
        symbol=stock,
        exchange=tradingview_settings.exchange,
        screener=tradingview_settings.screener
    )
    return handler.get_analysis().summary


def get_stock_actions(stocks: list[str]) -> list[StockAction]:
    stock_actions = []
    for stock in stocks:
        summary = __get_stock_summary(stock)
        if summary["RECOMMENDATION"] in (Recommendation.neutral, Recommendation.error):
            print(f"Stock {stock} not recommend to trading today")
            continue
        if summary["RECOMMENDATION"] in (Recommendation.buy, Recommendation.strong_buy):
            stock_actions.append(
                StockAction(
                    stock=stock,
                    action=Recommendation.buy
                )
            )
        elif summary["RECOMMENDATION"] in (Recommendation.sell, Recommendation.strong_sell):
            stock_actions.append(
                StockAction(
                    stock=stock,
                    action=Recommendation.sell
                )
            )
    return stock_actions








