import asyncio
import telegram
import aiohttp
from bs4 import BeautifulSoup, element
import datetime
from classes import ItemFromEbay
from utils.utils import parse_price_to_int, get_location_id, replace_umlauts
from constants import SCRAPE_URL, SCRAPE_INTERVAL
from classes import Customer
from utils.telegram_command_utils import send_notification
from utils.postgres_utils import fetch_for_scraping, check_if_item_exists_in_db, add_item_to_db
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

EBAY_KLEINANZEIGEN_URL = SCRAPE_URL


async def async_requests(
    chat_id: int, item: str, location: str, radius: int, bot: telegram.Bot
) -> BeautifulSoup | None:
    location = replace_umlauts(location).lower().strip().replace(" ", "-")
    loc_id = await get_location_id(location)
    if loc_id == None:
        logger.info(f"Location {location} not found.")
        await send_notification(
            msg=f"Location {location} not found. Please check the location.",
            chat_id=chat_id,
            bot=bot,
        )
        return None
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.47"
    }
    logger.info(
        f"Scraping data for {item} in {location} with radius {radius} km using the following URL: {EBAY_KLEINANZEIGEN_URL}{location}/{item}/k0{loc_id}r{radius}"
    )
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"{EBAY_KLEINANZEIGEN_URL}{location}/{item}/k0{loc_id}r{radius}", headers=header
        ) as response:
            html = await response.text()
            soup = BeautifulSoup(html, "html.parser")
            return soup


async def background_scraper(bot: telegram.Bot):
    while True:
        logger.info(f"Scraping data at: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        results = fetch_for_scraping()
        if not results:
            logger.info("No customers found for scraping.")
            await asyncio.sleep(SCRAPE_INTERVAL)
            continue
        scrape_tasks = []
        for result in results:
            task = asyncio.create_task(
                scrape_data_async(
                    customer=Customer(
                        chat_id=result[0],
                        item_name=result[1],
                        price_limit=result[2],
                        location=result[3],
                        radius=result[4],
                    ),
                    bot=bot,
                )
            )
            scrape_tasks.append(task)
        await asyncio.gather(*scrape_tasks)
        await asyncio.sleep(SCRAPE_INTERVAL)

# Add else case
async def scrape_data_async(customer: Customer, bot: telegram.Bot):
    soup = await async_requests(
        chat_id=customer.chat_id,
        item=customer.item_name,
        location=customer.location,
        radius=customer.radius,
        bot=bot,
    )
    if soup == None:
        logger.info(f"Scraping failed for {customer.item_name} in {customer.location}.")
        return
    for entry in soup.find_all("article", {"class": "aditem"}):
        item_from_ebay = find_item_information(entry=entry)
        if not check_if_item_exists_in_db(identifier=item_from_ebay.identifier):
            add_item_to_db(item_from_ebay)
            if item_from_ebay.price <= customer.price_limit:
                logger.info(f"Message sent to chat_id: {customer.chat_id}")
                msg = f"""✨ New Offer Found for {item_from_ebay.item_name}! ✨
🏷️ Item: {item_from_ebay.item_name}
💰 Price: {item_from_ebay.price}€
🔗 Link: {item_from_ebay.url}"""
                await send_notification(msg=msg, chat_id=customer.chat_id, bot=bot)


# Extract the information for items of a given soup tag and returns an instance of ItemFromEbay that contains all the data
def find_item_information(entry: element.PageElement) -> ItemFromEbay:
    split_string = str(entry["data-href"][11:]).split("/")
    item_name = split_string[0]
    identifier = split_string[1]
    url = f"{EBAY_KLEINANZEIGEN_URL[: len(EBAY_KLEINANZEIGEN_URL) - 2]}{entry['data-href'][1:]}"
    price_html = entry.find("p", {"class": "aditem-main--middle--price-shipping--price"})
    if price_html != None:
        price = parse_price_to_int(str(price_html.text.strip()))
    else:
        price = 0
    date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return ItemFromEbay(item_name=item_name, identifier=identifier, url=url, price=price, date=date)
