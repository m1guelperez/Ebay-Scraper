from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    filters,
    MessageHandler,
    Application,
    CallbackQueryHandler,
)
from rich.logging import RichHandler
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
    unsubscribe_and_remove_command,
    invalid_medium,
    delete_button_handler,
)
from ebayscraper.src.constants import TOKEN
import asyncio
import logging

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[RichHandler(rich_tracebacks=True, markup=True)],
)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def post_init(application: Application):
    """Create background task after bot initialization."""
    asyncio.create_task(background_scraper(application.bot))
    logger.info("Background scraper task created.")


# main method of the telegram bot
def main_telegram_bot() -> None:
    application = ApplicationBuilder().token(TOKEN).post_init(post_init=post_init).build()
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("init", init_command))
    application.add_handler(CommandHandler("add", add_command))
    application.add_handler(CommandHandler("remove", remove_command))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_and_remove_command))
    application.add_handler(CommandHandler("list", list_command))
    application.add_handler(CallbackQueryHandler(delete_button_handler, pattern=r"delete_search:"))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), no_command_message))
    application.add_handler(MessageHandler(filters.COMMAND, unknown_command))
    application.add_handler(MessageHandler((filters.VIDEO | filters.PHOTO), invalid_medium))
    application.add_error_handler(error_handler)
    application.run_polling()


if __name__ == "__main__":
    logger.info("Starting the eBay scraper Telegram bot...")
    main_telegram_bot()
