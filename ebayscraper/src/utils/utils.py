from ebayscraper.src.classes import Customer
import aiohttp
import json
import urllib.parse
import aiofiles


def replace_umlauts(string: str) -> str:
    string = string.replace("ä", "ae")
    string = string.replace("ö", "oe")
    string = string.replace("ü", "ue")
    string = string.replace("ß", "ss")
    return string


# Get values from the incoming telegram message using the /init command
def parse_item_message(chat_id: int, message: str) -> Customer | None:
    characteristics = message.split(",")
    command_end = 0
    # Remove the first element of the list, which is the command itself
    for i in characteristics[0]:
        command_end += 1
        if i == " ":
            break
    characteristics[0] = str(characteristics[0])[command_end:]
    if len(characteristics) < 4:
        return None
    item = characteristics[0].strip().lower().replace(" ", "-")
    item = replace_umlauts(item)
    pricelimit = int(characteristics[1].strip())
    location = characteristics[2].strip().lower()
    location = replace_umlauts(location)
    radius = int(characteristics[3].strip())
    return Customer(
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


def parse_remove_message(message: str) -> list | None:
    message = message.split(",")
    message[0] = str(message[0])[7:]
    if len(message) < 2:
        return None
    else:
        for item in range(len(message)):
            message[item] = message[item].lower().strip().replace(" ", "-")
        return message


# For change offers or items without a price tag, return 0.
def parse_price_to_int(price: str) -> int:
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


async def get_location_id(location: str) -> str | None:
    async with aiofiles.open("./location_ids.json", "r") as file:
        content = await file.read()
        location_ids = json.loads(content)
    if location in location_ids:
        print(f"Cache hit for '{location}'")
        return location_ids[location]
    async with aiohttp.ClientSession() as session:
        task = session.get(
            f"https://www.kleinanzeigen.de/s-ort-empfehlungen.json?query={urllib.parse.quote_plus(location)}"
        )
        async with task as response:
            if response.status == 200:
                data = await response.json()
                location_id = str(list(data.keys())[1]).replace(
                    "_", "l"
                )  # Get the second key from the dictionary which corresponds to the location. The first is germany.
                # The locations is returned as _299424, so we need to replace the _ with l.
                location_ids[location] = location_id
                content_to_write = json.dumps(location_ids, indent=4, ensure_ascii=False)
                async with aiofiles.open("./location_ids.json", "w") as file:
                    await file.write(content_to_write)
                print(f"Cache updated for '{location}' with ID '{location_id}'")
                return location_id
            else:
                return None
