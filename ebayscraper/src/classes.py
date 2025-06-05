from datetime import datetime
from dataclasses import dataclass
from typing import Self, Optional


@dataclass(slots=True)
class Item:
    item_name: str
    identifier: str
    url: str
    price: int
    last_seen_date: datetime
    item_id: Optional[int] = None

    def __str__(self) -> str:
        return f"{self.item_name} ({self.identifier}) - {self.price} EUR\n{self.url}\n{self.last_seen_date.strftime('%Y-%m-%d %H:%M:%S')}"

    @classmethod
    def from_db(cls, item_tuple: tuple) -> Self:
        return cls(
            item_id=item_tuple[0],
            identifier=item_tuple[1],
            item_name=item_tuple[2],
            price=item_tuple[3],
            url=item_tuple[4],
            last_seen_date=item_tuple[6],
        )


@dataclass(slots=True)
class User:
    chat_id: int

    def __str__(self) -> str:
        return f"Chat ID: {self.chat_id}\n"


@dataclass(slots=True)
class SearchRequest:
    chat_id: int
    item_name: str
    price_limit: int
    location: str
    radius: int
    search_id: Optional[int] = None

    def __str__(self) -> str:
        return (
            f"Chat ID: {self.chat_id}\n"
            f"Item Name: {self.item_name}\n"
            f"Price Limit: {self.price_limit} EUR\n"
            f"Location: {self.location}\n"
            f"Radius: {self.radius} km"
        )

    @classmethod
    def from_db(cls, search_tuple: tuple) -> Self:
        return cls(
            search_id=search_tuple[0],
            chat_id=search_tuple[1],
            item_name=search_tuple[2],
            price_limit=search_tuple[3],
            location=search_tuple[4],
            radius=search_tuple[5],
        )
