from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    filters,
    MessageHandler,
)
import threading
from telegram import Update
from scrape import scrape_data
from configurations import load_configfile
from configurations import TOKEN, CHANNEL_ID
from utils import user_exists_in_db, add_new_customer_values, parse_message

ITEMS = load_configfile("./items.toml")["items"]
LOCATION = load_configfile("./items.toml")["search_settings"]["location"]
RADIUS = load_configfile("./items.toml")["search_settings"]["radius"]
SAMIR_LIST = ["gtx-1050", "gtx-1050-ti", "gtx-1660", "gtx-1660-ti", "gtx-1660-super"]
GIADAS_LIST = ["iphone-13pro-max-256gb"]


async def start_function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        text="Hello! This is the EbayAlerts bot.\nTo get you started, please use the /init command and copy and fill the following message:\n"
        + "For example like that:",
        chat_id=update.effective_chat.id,
    )
    await context.bot.send_message(
        text="/init\n"
        + "Itemname: Gtx 1080\n"
        + "Pricelimit: 200 \n"
        + "Location: Köln\n"
        + "Radius (in km): 20",
        chat_id=update.effective_chat.id,
    )


async def init_first_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_exists_in_db(int(update.message.from_user.id)):
        print("User does not exist: " + str(update.message.from_user.id))
        customer_values = parse_message(int(update.message.from_user.id), update.message.text)
        add_new_customer_values(int(update.message.from_user.id), customer_values)
        await context.bot.send_message(
            text="Great it is initialized!",
            chat_id=update.effective_chat.id,
        )
    else:
        await context.bot.send_message(
            text="You already initialized the bot!\n"
            + "If you want to add a new item, please use the /add command.\n"
            + "If you want to remove an item, please use the /remove command.\n"
            + "If you need help, use the /help command.",
            chat_id=update.effective_chat.id,
        )


async def send_item_notification(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    message = "Use some commands to get started!"
    await context.bot.send_message(text=message, chat_id=chat_id)


async def add_item_to_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(text="Item successfully added!", chat_id=update.effective_chat.id)



async def remove_item_from_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(text="Item successfully removed!", chat_id=update.effective_chat.id)



# Handler if command isn't recognized
async def unknown(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command."
    )


# TODO: Make examples for each command.
async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="The following commands are available:\n"
        + "/start - Start the bot\n"
        + "/init - Initialize the bot\n"
        + "/add - Add an item to the watchlist\n"
        + "/remove - Remove an item from the watchlist",
    )


def main() -> None:
    thread = threading.Thread(target=scrape_data, args=(ITEMS, LOCATION, RADIUS))
    thread.start()
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start_function))
    application.add_handler(CommandHandler("init", init_first_item))
    application.add_handler(CommandHandler("add", add_item_to_watchlist))
    application.add_handler(CommandHandler("remove", remove_item_from_watchlist))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), send_item_notification)
    )
    application.add_handler(MessageHandler(filters.COMMAND, unknown))
    application.run_polling()

    thread.join()


if __name__ == "__main__":
    main()
