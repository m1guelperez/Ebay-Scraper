import asyncio
from time import sleep
import telegram
from scrape import scrape_data
from utils import load_configfile, parse_price_to_float

TOKEN = load_configfile("./creds.toml")["telegram"]["token"]
CHANNEL_ID = load_configfile("./creds.toml")["telegram"]["channelID"]
ITEMS = load_configfile("./items.toml")["items"]
LOCATION = load_configfile("./items.toml")["search_settings"]["location"]
RADIUS = load_configfile("./items.toml")["search_settings"]["radius"]
DATABASE_PWD = load_configfile("./creds.toml")["postgres"]["password"]
SAMIR_LIST = ["gtx-1050", "gtx-1050-ti", "gtx-1660", "gtx-1660-ti", "gtx-1660-super"]


async def main():
    bot = telegram.Bot(TOKEN)
    while True:
        for item in ITEMS:
            current_item = load_configfile("./items.toml")["items"][item]
            async with bot:
                list_of_new_items = scrape_data(DATABASE_PWD, current_item, LOCATION, RADIUS)
                if len(list_of_new_items) > 1:
                    msg = "{} new deal(s) for {}!".format(len(list_of_new_items), current_item)
                    await bot.send_message(
                        text=msg,
                        chat_id=CHANNEL_ID,
                    )
                elif len(list_of_new_items) == 1:
                    if current_item in SAMIR_LIST and parse_price_to_float(list_of_new_items[0].price) <= 200.0:
                        msg = "A new {} for {}!\nLink: {}".format(
                            current_item, list_of_new_items[0].price, list_of_new_items[0].url
                        )
                        await bot.send_message(
                            text=msg,
                            chat_id=CHANNEL_ID,
                        )
                    else:
                        msg = "A new {} for {}!\nLink: {}".format(
                            current_item, list_of_new_items[0].price, list_of_new_items[0].url
                        )
                        await bot.send_message(
                            text=msg,
                            chat_id=CHANNEL_ID,
                        )
        sleep(150)
        print("Woke up")


if __name__ == "__main__":
    asyncio.run(main())
