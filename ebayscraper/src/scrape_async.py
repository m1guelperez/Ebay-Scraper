import bs4
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import datetime
from classes import ItemFromEbay
from utils.utils import parse_price_to_int, get_location_id, replace_umlauts
from constants import SCRAPE_URL, SCRAPE_INTERVAL
from classes import Customer
from utils.telegram_command_utils import send_notification
from utils.postgres_utils import fetch_for_scraping, check_if_item_exists_in_db, add_item_to_db

EBAY_KLEINANZEIGEN = SCRAPE_URL


async def async_requests(
    chat_id: int, item: str, location: str, radius: str
) -> BeautifulSoup | None:
    location = replace_umlauts(location).lower().strip().replace(" ", "-")
    loc_id = await get_location_id(location)
    if loc_id == None:
        print(f"Location {location} not found.")
        await send_notification(
            msg=f"Location {location} not found. Please check the location.",
            chat_id=chat_id,
        )
        return None
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.47"
    }
    print(
        f"Scraping data for {item} in {location} with radius {radius} km using the following URL: {EBAY_KLEINANZEIGEN}{location}/{item}/k0{loc_id}r{radius}"
    )
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{EBAY_KLEINANZEIGEN}{location}/{item}/k0{loc_id}r{radius}", headers=header
        ) as response:
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            return soup


async def background_scraper():
    while True:
        print(f"Scraping data at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        results = fetch_for_scraping()
        scrape_tasks = []
        for result in results:
            task = asyncio.create_task(
                scrape_data_async(
                    Customer(
                        chat_id=result[0],
                        item_name=result[1],
                        price_limit=result[2],
                        location=result[3],
                        radius=result[4],
                    ),
                )
            )
            scrape_tasks.append(task)
        await asyncio.gather(*scrape_tasks)
        await asyncio.sleep(SCRAPE_INTERVAL)


async def scrape_data_async(customer: Customer):
    soup = await async_requests(
        chat_id=customer.chat_id,
        item=customer.item_name,
        location=customer.location,
        radius=customer.radius,
    )
    if soup == None:
        print(f"Scraping failed for {customer.item_name} in {customer.location}.")
        return
    for entry in soup.find_all("article", {"class": "aditem"}):
        item_from_ebay = find_item_information(entry=entry)
        if not check_if_item_exists_in_db(identifier=item_from_ebay.identifier):
            add_item_to_db(item_from_ebay)
            if item_from_ebay.price <= customer.price_limit:
                print(
                    f"Message sent at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} to chat_id: {customer.chat_id}"
                )
                msg = f"""✨ New Offer Found! ✨
🏷️ Item: {item_from_ebay.item_name}
💰 Price: {item_from_ebay.price}€
🔗 Link: {item_from_ebay.url}"""
                await send_notification(msg=msg, chat_id=customer.chat_id)


# Extract the information for items of a given soup tag and returns an instance of ItemFromEbay that contains all the data
def find_item_information(entry: bs4.element.Tag) -> ItemFromEbay:
    split_string = str(entry["data-href"][11:]).split("/")
    item_name = split_string[0]
    identifier = split_string[1]
    url = EBAY_KLEINANZEIGEN[: len(EBAY_KLEINANZEIGEN) - 2] + str(entry["data-href"])[1:]
    price_html = entry.find("p", {"class": "aditem-main--middle--price-shipping--price"})
    if price_html != None:
        price = parse_price_to_int(str(price_html.text.strip()))
    else:
        price = 0
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return ItemFromEbay(item_name=item_name, identifier=identifier, url=url, price=price, date=date)
