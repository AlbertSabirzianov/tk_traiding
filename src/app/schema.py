from typing import Literal

from pydantic import BaseModel


class StockAction(BaseModel):
    stock: str
    action: Literal["BUY", "SELL"]


