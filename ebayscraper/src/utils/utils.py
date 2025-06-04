from ebayscraper.src.classes import User
import aiohttp
import json
import urllib.parse
import aiofiles
from ebayscraper.src.utils.machine_learning import extract_customer_values_with_ml
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def replace_umlauts(string: str) -> str:
    string = string.replace("ä", "ae")
    string = string.replace("ö", "oe")
    string = string.replace("ü", "ue")
    string = string.replace("ß", "ss")
    return string


# Get values from the incoming telegram message using the /init command
def parse_item_schema_message(chat_id: int, message: str) -> User | None:
    message_parts = message.split(",")
    # Remove the command part from the message
    message_parts[0] = message_parts[0].strip().split(" ")[1].strip()
    if len(message_parts) < 4:
        return None
    item = message_parts[0].strip().lower().replace(" ", "-")
    item = replace_umlauts(item)
    pricelimit = int(message_parts[1].strip())
    location = message_parts[2].strip().lower()
    location = replace_umlauts(location)
    radius = int(message_parts[3].strip())
    return User(
        chat_id=chat_id,
        item_name=item,
        price_limit=pricelimit,
        location=location,
        radius=radius,
    )


def parse_update_message(message: str) -> list:
    update_values = message.splitlines()
    updates = []
    for values in update_values:
        (value, update) = values.split(":")
        value = value.strip()
        update = update.strip()
        if isinstance(update, str):
            update = replace_umlauts(update)
        updates.append((value, update))
    return updates


def parse_remove_message(message: str) -> list[str]:
    message_as_list = message.split(
        ","
    )  # Because of the '/remove' command, the message is split by commas.
    message_as_list[0] = (
        message_as_list[0].strip().split()[1].strip()
    )  # Remove the '/remove' command from the list.
    message_as_list = [
        replace_umlauts(msg).lower().strip().replace(" ", "-") for msg in message_as_list
    ]
    return message_as_list


# For change offers or items without a price tag, return 0.
def parse_price_to_int(price: str) -> int:
    cleared_string = ""
    price = price.replace("\n", "").replace(" ", "")
    if len(price.strip()) != 0:
        for x in price:
            if x.isdigit():
                cleared_string += str(x)
            if (
                x == "V" or x == "€"
            ):  # Old prices are also stored in the string. The price looks like this: "1.650€VB2.000€" and prices without a price tag look like this: "VB"
                break
        if len(cleared_string) != 0:
            return int(cleared_string)
    return 0


async def get_location_id(location: str) -> str | None:
    async with aiofiles.open("./location_ids.json", "r") as file:
        content = await file.read()
        location_ids = json.loads(content)
    if location in location_ids:
        logger.info(f"Cache hit for '{location}'")
        return location_ids[location]
    url = f"https://www.kleinanzeigen.de/s-ort-empfehlungen.json?query={urllib.parse.quote_plus(location)}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                keys = list(data.keys())
                if len(keys) < 2:
                    logger.info(f"Location '{location}' not found.")
                    return None
                location_id = str(keys[1]).replace(
                    "_", "l"
                )  # Get the second key from the dictionary which corresponds to the location. The first is germany.
                # The locations is returned as _299424, so we need to replace the _ with l.
                location_ids[location] = location_id
                content_to_write = json.dumps(location_ids, indent=4, ensure_ascii=False)
                async with aiofiles.open("./location_ids.json", "w") as file:
                    await file.write(content_to_write)
                logger.info(f"Cache updated for '{location}' with ID '{location_id}'")
                return location_id
            else:
                logger.error(f"Error fetching location ID for '{location}': {response.status}")
                return None


def is_schema_format(string: str) -> bool:
    """
    Check if the string is in JSON schema format.
    """
    if len(string.split(",")) == 4:
        return True
    return False


def extract_customer_values(chat_message: str, chat_id: int) -> User | None:
    if is_schema_format(chat_message):
        logger.info("Using schema format to extract customer values.")
        customer_values = parse_item_schema_message(chat_id, chat_message)
    else:
        logger.info("Using machine learning model to extract customer values.")
        customer_values = extract_customer_values_with_ml(
            chat_id=chat_id, chat_message=chat_message
        )
    if customer_values is None:
        logger.error("Error: Could not extract customer values from message.")
        return None
    return customer_values
