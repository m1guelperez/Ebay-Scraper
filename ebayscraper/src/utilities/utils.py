from ebayscraper.src.classes import Customer


def replace_umlauts(string: str):
    string = string.replace("ä", "ae")
    string = string.replace("ö", "oe")
    string = string.replace("ü", "ue")
    string = string.replace("ß", "ss")
    return string


# Get values from the incoming telegram message using the /init command
def parse_item_message(chat_id: int, message: str):
    characteristics = message.splitlines()
    item = (characteristics[1].split(":")[1].strip()).lower().replace(" ", "-")
    item = replace_umlauts(item)
    pricelimit = int(characteristics[2].split(":")[1].strip())
    location = (characteristics[3].split(":")[1].strip()).lower()
    location = replace_umlauts(location)
    radius = int(characteristics[4].split(":")[1].strip())
    return Customer(
        chat_id=chat_id,
        item_name=item,
        price_limit=pricelimit,
        location=location,
        radius=radius,
    )


def parse_update_message(chat_id: int, message: str) -> list:
    update_values = message.splitlines()
    updates = []
    for values in update_values:
        (value, update) = values.split(":")
        value = value.strip()
        update = update.strip()
        if isinstance(update, str):
            update = replace_umlauts(update)
        updates.append((value, update))
        print(updates)


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


custom = Customer(2873, "gtx-0189", 50, "Müchen", 233)
print(custom.item_name)
