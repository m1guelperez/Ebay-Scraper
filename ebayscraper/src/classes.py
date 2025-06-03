from datetime import datetime


class ItemFromEbay:
    item_name: str
    identifier: str
    url: str
    price: int
    date: datetime

    def __init__(self, item_name: str, identifier: str, url: str, price: int, date: str):
        self.item_name = item_name
        self.identifier = identifier
        self.price = price
        self.url = url
        self.date = datetime.strptime(date, "%Y-%m-%d %H:%M:%S")

    def __repr__(self) -> str:
        return f"ItemFromEbay(item_name='{self.item_name}', identifier='{self.identifier}', url='{self.url}', price={self.price}, date={self.date})"


class Customer:
    chat_id: int
    item_name: str
    price_limit: int
    location: str
    radius: int

    def __init__(self, chat_id: int, item_name: str, price_limit: int, location: str, radius: int):
        self.chat_id = chat_id
        self.item_name = item_name
        self.price_limit = price_limit
        self.location = location
        self.radius = radius

    def __repr__(self) -> str:
        return f"Customer(chat_id={self.chat_id}, item_name='{self.item_name}', price_limit={self.price_limit}, location='{self.location}', radius={self.radius})"
