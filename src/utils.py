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


# Get values from the incoming telegram message using the /init command
def parse_message(chat_id: int, message: str):
    characteristics = message.splitlines()
    itemname = (characteristics[1].split(":")[1].strip()).lower().replace(" ", "-")
    itemname = replace_umlauts(itemname)
    pricelimit = int(characteristics[2].split(":")[1].strip())
    location = characteristics[3].split(":")[1].strip()
    radius = int(characteristics[4].split(":")[1].strip())
    return Customer(
        chat_id=chat_id,
        item_name=itemname,
        price_limit=pricelimit,
        location=location,
        radius=radius,
    )


def replace_umlauts(string: str):
    string = string.replace("ä", "ae")
    string = string.replace("ö", "oe")
    string = string.replace("ü", "ue")
    string = string.replace("ß", "ss")
    return string


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

# Used as initializing for the new customer (/init command in telegram)
def add_new_customer_values(user_id: int, customer: Customer):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO customer (chat_id,item_name,item_price_limit,location,radius)
        VALUES (%s,%s,%s,%s,%s);""",
        (user_id, customer.item_name, customer.price_limit, customer.location, customer.radius),
    )
    conn.commit()
    close_db_connections(cur=cur, connection=conn)


def user_exists_in_db(chat_id: int):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("""SELECT chat_id FROM customer WHERE chat_id = (%s);""", (chat_id,))
    res_of_sql_exc = cur.fetchone()
    if res_of_sql_exc == None:
        return False
    else:
        return True

#TODO: Finish the thread function
def thread_scraping():
    conn = connect_to_db()
    curr = conn.cursor()
    while True:
        curr.execute("""SELECT item_name FROM customer;""")
        res_of_sql_exc = curr.fetchall()
        for item in res_of_sql_exc:
            print(str(item).replace("(", "").replace(")", "").replace(",", "").replace("'", ""))

thread_scraping()