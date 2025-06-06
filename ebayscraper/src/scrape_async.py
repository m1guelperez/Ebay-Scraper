import asyncio
import telegram
import aiohttp
from bs4 import BeautifulSoup, element
import datetime
from classes import Item
from utils.utils import parse_price_to_int, get_location_id, replace_umlauts
from constants import SCRAPE_URL, SCRAPE_INTERVAL
from classes import SearchRequest, Item
from utils.telegram_command_utils import send_notification
from utils.postgres_utils import (
    fetch_for_scraping,
    get_item_via_id_from_db,
    check_if_notification_already_sent_db,
    add_item_to_db,
    add_notification_sent_db,
)
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
            logger.info("No requests found for scraping.")
            await asyncio.sleep(SCRAPE_INTERVAL)
            continue
        scrape_tasks = []
        for result in results:
            task = asyncio.create_task(
                scrape_data_async(
                    search_request=SearchRequest.from_db(search_tuple=result),
                    bot=bot,
                )
            )
            scrape_tasks.append(task)
        await asyncio.gather(*scrape_tasks)
        await asyncio.sleep(SCRAPE_INTERVAL)


# Add else case
async def scrape_data_async(search_request: SearchRequest, bot: telegram.Bot):
    soup = await async_requests(
        chat_id=search_request.chat_id,
        item=search_request.item_name,
        location=search_request.location,
        radius=search_request.radius,
        bot=bot,
    )
    if soup == None:
        logger.info(f"Scraping failed for {search_request.item_name} in {search_request.location}.")
        return
    for entry in soup.find_all("article", {"class": "aditem"}):
        db_item_id = None
        item_from_ebay = find_item_information(entry=entry)
        existing_item = get_item_via_id_from_db(identifier=item_from_ebay.identifier)
        if not existing_item:
            db_item_id = add_item_to_db(item_from_ebay)
            logger.info(
                f"Item {item_from_ebay.item_name} added to the database with ID {db_item_id}."
            )
        else:
            db_item_id = existing_item.item_id
            logger.debug(
                f"Item {item_from_ebay.item_name} already exists in the database with ID {db_item_id}."
            )

        if item_from_ebay.price > search_request.price_limit:
            logger.debug(
                f"Item {item_from_ebay.item_name} exceeds price limit of {search_request.price_limit}€."
            )
            continue

        if check_if_notification_already_sent_db(
            search_id=search_request.search_id, item_id=db_item_id
        ):
            logger.debug(
                f"Notification for item {item_from_ebay.item_name} with ID {db_item_id} already sent."
            )
            continue

        if item_from_ebay.price <= search_request.price_limit:
            logger.info(f"Message sent to chat_id: {search_request.chat_id}")
            msg = f"""✨ New Offer Found for {search_request.item_name}! ✨
💰 Price: {item_from_ebay.price}€
🔗 Link: {item_from_ebay.url}"""
            await send_notification(msg=msg, chat_id=search_request.chat_id, bot=bot)
            add_notification_sent_db(search_id=search_request.search_id, item_id=db_item_id)


# Extract the information for items of a given soup tag and returns an instance of ItemFromEbay that contains all the data
def find_item_information(entry: element.PageElement) -> Item:
    split_string = str(entry["data-href"][11:]).split("/")
    item_name = split_string[0]
    identifier = split_string[1]
    url = f"{EBAY_KLEINANZEIGEN_URL[: len(EBAY_KLEINANZEIGEN_URL) - 2]}{entry['data-href'][1:]}"
    price_html = entry.find("p", {"class": "aditem-main--middle--price-shipping--price"})
    if price_html != None:
        price = parse_price_to_int(str(price_html.text.strip()))
    else:
        price = 0
    return Item(
        item_name=item_name,
        identifier=identifier,
        url=url,
        price=price,
        last_seen_date=datetime.datetime.now(),
    )
