from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    filters,
    MessageHandler,
    Application,
)
from scrape_async import background_scraper
from utils.telegram_command_utils import (
    start_command,
    init_command,
    add_command,
    remove_command,
    list_command,
    no_command_message,
    unknown_command,
    error_handler,
    help_command,
    remove_all_command,
)
from ebayscraper.src.constants import TOKEN
import asyncio


async def post_init(application: Application):
    """Create background task after bot initialization."""
    asyncio.create_task(background_scraper())
    print("Background scraper task started.")


# main method of the telegram bot
def main_telegram_bot() -> None:
    application = ApplicationBuilder().token(TOKEN).post_init(post_init=post_init).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("init", init_command))
    application.add_handler(CommandHandler("add", add_command))
    application.add_handler(CommandHandler("remove", remove_command))
    application.add_handler(CommandHandler("removeall", remove_all_command))
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), no_command_message))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    application.add_error_handler(error_handler)
    application.run_polling()


if __name__ == "__main__":
    main_telegram_bot()
