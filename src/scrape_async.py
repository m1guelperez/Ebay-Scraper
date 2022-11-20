import bs4
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import datetime
from classes import ItemFromEbay
from utils import parse_price_to_float
from postgres_utils import connect_to_db, close_db_connections

EBAY_KLEINANZEIGEN = "https://www.ebay-kleinanzeigen.de/s-"


async def async_requests(item: str, location: str, radius: str) -> BeautifulSoup:
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.47"
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(
            EBAY_KLEINANZEIGEN + location + "/" + item + "/k0l1185r" + radius, headers=header
        ) as response:
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            return soup


# Wrapper function such that we scrape data every 150 seconds
async def wrap_in_inf_loop():
    while True:
        await scrape_data_async(item="iphone 13", location="muenchen", radius="50")
        await asyncio.sleep(120)


def create_asnyc_loop():
    loop = asyncio.new_event_loop()
    loop.run_until_complete(wrap_in_inf_loop())


async def scrape_data_async(item: str, location: str, radius: str) -> int:
    soup = await async_requests(item=item, location=location, radius=radius)
    for entry in soup.find_all("article", {"class": "aditem"}):
        item_from_ebay = find_item_information(entry=entry)
        print(item_from_ebay.identifier)


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
