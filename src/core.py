from time import sleep
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    filters,
    MessageHandler,
)
from telegram import Update
from scrape import scrape_data
from configurations import load_configfile
from configurations import TOKEN, CHANNEL_ID
from utils import user_exists_in_db, add_new_user

ITEMS = load_configfile("./items.toml")["items"]
LOCATION = load_configfile("./items.toml")["search_settings"]["location"]
RADIUS = load_configfile("./items.toml")["search_settings"]["radius"]
SAMIR_LIST = ["gtx-1050", "gtx-1050-ti", "gtx-1660", "gtx-1660-ti", "gtx-1660-super"]
GIADAS_LIST = ["iphone-13pro-max-256gb"]


async def start_function(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not user_exists_in_db(int(update.message.from_user.id)):
        add_new_user(int(update.message.from_user.id))
    await context.bot.send_message(
        text="Hello! This is the EbayAlerts bot.", chat_id=update.effective_chat.id
    )


async def send_item_notification(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    message = ""
    await context.bot.send_message(text=message, chat_id=chat_id)


async def add_item_to_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return 10


async def remove_item_from_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    return 10


def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start_function))
    application.add_handler(CommandHandler("add", add_item_to_watchlist))
    application.add_handler(CommandHandler("remove", remove_item_from_watchlist))
    application.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), send_item_notification)
    )
    application.run_polling()


if __name__ == "__main__":
    main()
