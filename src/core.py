import asyncio
from time import sleep
import telegram
from scrape import scrape_data
import datetime
from utils import load_configfile
from configurations import TOKEN, CHANNEL_ID

ITEMS = load_configfile("./items.toml")["items"]
LOCATION = load_configfile("./items.toml")["search_settings"]["location"]
RADIUS = load_configfile("./items.toml")["search_settings"]["radius"]
SAMIR_LIST = ["gtx-1050", "gtx-1050-ti", "gtx-1660", "gtx-1660-ti", "gtx-1660-super"]
GIADAS_LIST = ["iphone-13pro-max-256gb"]


async def main():
    bot = telegram.Bot(TOKEN)
    while True:
        print("Start crawling for: " + str(datetime.datetime.now()))
        for item in ITEMS:
            current_item = load_configfile("./items.toml")["items"][item]
            async with bot:
                list_of_new_items = scrape_data(current_item, LOCATION, RADIUS)
                if len(list_of_new_items) > 1:
                    print("Msg send")
                    msg = "{} new deal(s) for {}€!".format(len(list_of_new_items), current_item)
                    await bot.send_message(
                        text=msg,
                        chat_id=CHANNEL_ID,
                    )
                elif len(list_of_new_items) == 1:
                    if current_item in SAMIR_LIST and list_of_new_items[0].price <= 200.0:
                        print("Msg send")
                        msg = "A new {} for {}€!\nLink: {}".format(
                            current_item, list_of_new_items[0].price, list_of_new_items[0].url
                        )
                        await bot.send_message(
                            text=msg,
                            chat_id=CHANNEL_ID,
                        )
                    elif current_item in GIADAS_LIST and list_of_new_items[0].price <= 1000.0:
                        print("Msg send")
                        msg = "@gigglexyz A new {} for {}€!\nLink: {}".format(
                            current_item, list_of_new_items[0].price, list_of_new_items[0].url
                        )
                        await bot.send_message(
                            text=msg,
                            chat_id=CHANNEL_ID,
                        )
                    elif (
                        current_item not in GIADAS_LIST
                        and current_item not in SAMIR_LIST
                        and list_of_new_items[0].price <= 600
                    ):
                        print("Msg send")
                        msg = "@GIG_0 A new {} for {}€!\nLink: {}".format(
                            current_item, list_of_new_items[0].price, list_of_new_items[0].url
                        )
                        await bot.send_message(
                            text=msg,
                            chat_id=CHANNEL_ID,
                        )
        sleep(150)


if __name__ == "__main__":
    asyncio.run(main())
