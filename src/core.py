import asyncio
from time import sleep
import telegram
from scrape import scrape
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
                number_of_new_items = scrape(DATABASE_PWD, current_item)
                if number_of_new_items != 0:
                    msg = "{} new deal(s) for {}!".format(
                        str(number_of_new_items), current_item
                    )
                    await bot.send_message(
                        text=msg,
                        chat_id=CHANNEL_ID,
                    )
        sleep(300)
        print("Woke up")


if __name__ == "__main__":
    asyncio.run(main())
