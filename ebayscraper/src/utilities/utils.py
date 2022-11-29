from ebayscraper.src.classes import Customer


def replace_umlauts(string: str):
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


parse_item_message(1, "/add RTX 3080, 600, Jüchen, 50")


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


# parse_remove_message("/remove item1")

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
