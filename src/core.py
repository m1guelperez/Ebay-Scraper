from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    filters,
    MessageHandler,
)
import threading
from scrape_async import *
from telegram_command_utils import *
from configurations import TOKEN
from utils import parse_message


def main_telegram_bot() -> None:
    application = ApplicationBuilder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start_function))
    application.add_handler(CommandHandler("init", init_first_item))
    application.add_handler(CommandHandler("add", add_item_to_watchlist))
    application.add_handler(CommandHandler("remove", remove_item_from_watchlist))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), no_command_message))
    application.add_handler(MessageHandler(filters.COMMAND, unknown))
    application.run_polling()


if __name__ == "__main__":
    # Thread that scrapes data
    thread = threading.Thread(target=create_asnyc_loop)
    thread.start()
    # main method for telegram bot in main thread that polls continuously
    main_telegram_bot()
    thread.join()
