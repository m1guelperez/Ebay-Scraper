import bs4
import requests
from bs4 import BeautifulSoup
import datetime

from utils import ItemFromEbay, parse_price_to_float
from postgres_utils import connect_to_db, close_db_connections

# TODO: define it once and clear
EBAY_KLEINANZEIGEN = "https://www.ebay-kleinanzeigen.de/s-"

# Makes a request, given the location and radius parameter
def make_request(item: str, location: str, radius: str) -> BeautifulSoup:
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.47"
    }
    ebay_request = requests.get(
        EBAY_KLEINANZEIGEN + location + "/" + item + "/k0l1185r" + radius,
        headers=header,
    )
    soup = BeautifulSoup(ebay_request.content, "html.parser")
    return soup


# Scrape the data after a we made a request and put it into the database if it doesn't exist yet.
def scrape_data(item: str, location: str, radius: str) -> int:
    soup = make_request(item=item, location=location, radius=radius)
    conn = connect_to_db()
    cur = conn.cursor()
    list_of_new_items = []
    for entry in soup.find_all("article", {"class": "aditem"}):
        ItemFromEbay = find_item_information(entry=entry)
        cur.execute(
            """SELECT item_name FROM items WHERE identifier = (%s);""", (ItemFromEbay.identifier,)
        )
        res_of_sql_exc = cur.fetchone()
        if res_of_sql_exc == None:
            cur.execute(
                """INSERT INTO items(item_name,date_of_input,price,url,identifier)
                VALUES (%s,%s,%s,%s,%s);""",
                (
                    ItemFromEbay.item_name,
                    ItemFromEbay.date,
                    ItemFromEbay.price,
                    ItemFromEbay.url,
                    ItemFromEbay.identifier,
                ),
            )
            list_of_new_items.append(ItemFromEbay)
    conn.commit()
    close_db_connections(cur=cur, connection=conn)
    return list_of_new_items


# Recieves a tag (part of a soup) and finds all the necesarry information of the item we are looking for.
def find_item_information(entry: bs4.element.Tag) -> ItemFromEbay:
    split_string = str(entry["data-href"][11:]).split("/")
    item_name = split_string[0]
    identifier = split_string[1]
    url = EBAY_KLEINANZEIGEN[: len(EBAY_KLEINANZEIGEN) - 2] + str(entry["data-href"])[1:]
    price_html = entry.find("p", {"class": "aditem-main--middle--price-shipping--price"})
    if price_html != None:
        price = parse_price_to_float(str(price_html.text.strip()))
    else:
        price = 0
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return ItemFromEbay(item_name=item_name, identifier=identifier, url=url, price=price, date=date)