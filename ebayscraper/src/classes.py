import datetime


class ItemFromEbay:
    item_name: str
    identifier: str
    url: str
    price: int
    date: datetime

    def __init__(self, item_name: str, identifier: str, url: str, price: int, date: datetime):
        self.item_name = item_name
        self.identifier = identifier
        self.price = price
        self.url = url
        self.date = date


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
