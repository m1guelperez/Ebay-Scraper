from datetime import datetime
import toml
import psycopg2
from typing import MutableMapping
import psycopg2.extensions


def load_configfile(path: str) -> MutableMapping:
    return toml.load(path)


def connect_to_db(pwd: str) -> psycopg2.extensions.connection:
    conn = psycopg2.connect(
        database="EbayItems",
        user="postgres",
        password=pwd,
        host="127.0.0.1",
        port="5432",
    )
    return conn


def close_connections(cur: psycopg2.extensions.cursor, connection: psycopg2.extensions.connection):
    cur.close()
    connection.close()


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
