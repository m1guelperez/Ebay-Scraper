import asyncio
from time import sleep
import telegram
from scrape import scrape_data
from utils import load_configfile

TOKEN = load_configfile("./creds.toml")["telegram"]["token"]
CHANNEL_ID = load_configfile("./creds.toml")["telegram"]["channelID"]
ITEMS = load_configfile("./items.toml")["items"]
DATABASE_PWD = load_configfile("./creds.toml")["postgres"]["password"]

async def main():
    bot = telegram.Bot(TOKEN)
    while True:
        for item in ITEMS:
            current_item = load_configfile("./items.toml")["items"][item]
            async with bot:
                list_of_new_items = scrape_data(DATABASE_PWD, current_item)
                if len(list_of_new_items) > 1:
                    msg = "{} new deal(s) for {}!".format(len(list_of_new_items), current_item)
                    await bot.send_message(
                        text=msg,
                        chat_id=CHANNEL_ID,
                    )
                elif len(list_of_new_items) == 1:
                    msg = "A new {} for {}!\nLink: {}".format(
                        current_item, list_of_new_items[0].price, list_of_new_items[0].url
                    )
                    await bot.send_message(
                        text=msg,
                        chat_id=CHANNEL_ID,
                    )
        sleep(300)
        print("Woke up")


if __name__ == "__main__":
    asyncio.run(main())
