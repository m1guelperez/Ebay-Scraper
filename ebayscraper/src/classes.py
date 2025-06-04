from datetime import datetime
from dataclasses import dataclass


@dataclass(slots=True)
class ItemFromEbay:
    item_name: str
    identifier: str
    url: str
    price: int
    date: datetime

    def __str__(self) -> str:
        return f"{self.item_name} ({self.identifier}) - {self.price} EUR\n{self.url}\n{self.date.strftime('%Y-%m-%d %H:%M:%S')}"


@dataclass(slots=True)
class User:
    chat_id: int
    item_name: str
    price_limit: int
    location: str
    radius: int

    def __str__(self) -> str:
        return (
            f"Chat ID: {self.chat_id}\n"
            f"Item Name: {self.item_name}\n"
            f"Price Limit: {self.price_limit} EUR\n"
            f"Location: {self.location}\n"
            f"Radius: {self.radius} km"
        )
