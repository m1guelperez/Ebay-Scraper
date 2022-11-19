from datetime import datetime
import toml
from typing import MutableMapping
from postgres_utils import connect_to_db, close_db_connections


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


def load_configfile(path: str) -> MutableMapping:
    return toml.load(path)


# For change offers or items without a price tag, return 0.
def parse_price_to_float(price: str) -> int:
    cleared_string = ""
    if len(price.strip()) != 0:
        for x in price:
            if x.isdigit():
                cleared_string += str(x)
        if len(cleared_string) != 0:
            return int(cleared_string)
        else:
            return 0
    else:
        return 0


def item_is_relevant(price_limit: int, item: ItemFromEbay):
    if item.price <= price_limit:
        return True
    else:
        return False


def add_new_user(user_id: int):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO info (chat_id,item_name,price_limit,location,radius)
        VALUES (%s,%s,%s,%s);""",
        (user_id, 0, "", ""),
    )
    conn.commit()
    close_db_connections(cur=cur, connection=conn)


def user_exists_in_db(user_id: int):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("""SELECT user_id FROM users WHERE user_id = (%s);""", (user_id))
    res_of_sql_exc = cur.fetchone()
    if res_of_sql_exc == None:
        return False
    else:
        return True