from telegram.ext import ContextTypes
from telegram import Update
import traceback
import telegram
from utils.utils import (
    parse_update_message,
    parse_remove_message,
    extract_customer_values,
)
from constants import RADIUS
from utils.postgres_utils import (
    add_customer_values_to_db,
    user_exists_in_db,
    entry_in_customer_db_exists,
    remove_customer_from_db,
    get_all_items_by_user_from_db,
    update_values_in_customer_db,
    remove_item_from_customer_db,
)
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


# /start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        logger.error("Error: effective_chat is None in start_command")
        return
    logger.info(f"Got start command from {update.effective_chat.id}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"""Hello! This is the EbayAlerts bot.
To get you started, please use the /init command and copy and fill the following message:
The radius has to be one of the following values: {RADIUS}.
For example like that:

/init item, pricelimit, location, radius
for example like:
/init GTX 1080, 650, Köln, 20
/init Ich suche ein iPhone 12, für 500 Euro, in Berlin in 30 km radius.""",
    )


# /init command
async def init_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        logger.error("Error: effective_chat is None in init_command")
        return
    logger.info(f"Got init command from {update.effective_chat.id}")
    if update.message is None or update.message.text is None:
        logger.error("Error: update.message or update.message.text is None in init_command")
        return
    customer_values = extract_customer_values(
        chat_message=update.message.text, chat_id=update.effective_chat.id
    )
    if customer_values is None:
        await context.bot.send_message(
            text=(
                """Please use the following format:
"/init item, pricelimit, location, radius
"/init GTX 1080, 650, Köln, 20
/init Ich suche ein iPhone 12, für 500 Euro, in Berlin in 30 km radius."""
            ),
            chat_id=update.effective_chat.id,
        )
        return
    if customer_values.radius not in RADIUS:
        await context.bot.send_message(
            text=f"The radius has to be: {RADIUS}!",
            chat_id=update.effective_chat.id,
        )
        return
    if not user_exists_in_db(int(update.message.from_user.id)):
        logger.info(f"User does not exist in db, creating new user for {update.effective_chat.id}")
        add_customer_values_to_db(int(update.message.from_user.id), customer_values)
        logger.info(f"Successfully added user {update.effective_chat.id} to db")
        await context.bot.send_message(
            text="Great user is initialized!",
            chat_id=update.effective_chat.id,
        )
    else:
        await context.bot.send_message(
            text="""You already initialized the bot! 
If you want to add a new item, please use the /add command.
If you want to remove an item, please use the /remove command. 
If you want to update an item, please use the /update command. 
If you want to list all your items, please use the /list command. 
If you want to remove all your items, please use the /removeall command. 
If you need help, use the /help command.""",
            chat_id=update.effective_chat.id,
        )


# for everything different then a command
async def no_command_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        logger.error("Error: effective_chat is None in no_command_message")
        return
    logger.info(f"Got no command message from {update.effective_chat.id}")
    message = "Use some commands to get started!"
    await context.bot.send_message(text=message, chat_id=update.effective_chat.id)


# /add command
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        logger.error("Error: effective_chat is None in add_command")
        return
    logger.info(f"Got add command from {update.effective_chat.id}")
    customer_values = extract_customer_values(
        chat_message=update.message.text, chat_id=update.effective_chat.id
    )
    if customer_values == None:
        await context.bot.send_message(
            text=(
                """Please use the following format:
"/add item, pricelimit, location, radius
"/add GTX 1080, 650, Köln, 20"""
            ),
            chat_id=update.effective_chat.id,
        )
        return
    if customer_values.radius not in RADIUS:
        await context.bot.send_message(
            text=f"The radius has to be: {RADIUS}!",
            chat_id=update.effective_chat.id,
        )
        return
    if not entry_in_customer_db_exists(int(update.message.from_user.id), customer_values.item_name):
        add_customer_values_to_db(int(update.message.from_user.id), customer_values)
        await context.bot.send_message(
            text=f"'{customer_values.item_name.capitalize()}' with a price limit of {customer_values.price_limit}€ and a radius of {customer_values.radius} km in {customer_values.location} successfully added to your watchlist!",
            chat_id=update.effective_chat.id,
        )
    else:
        await context.bot.send_message(
            text=f"'{customer_values.item_name.capitalize()}' already exists in your watchlist!",
            chat_id=update.effective_chat.id,
        )


# /remove command
async def remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        logger.error("Error: effective_chat is None in remove_command")
        return
    logger.info(f"Got remove command from {update.effective_chat.id}")
    items = parse_remove_message(update.message.text)
    if items == None:
        await context.bot.send_message(
            text="""Please use the following format:
/remove item1, item2, item3
/remove GTX 1080, GTX 1070, GTX 1060""",
            chat_id=update.effective_chat.id,
        )
    else:
        for item in items:
            if entry_in_customer_db_exists(int(update.message.from_user.id), item):
                remove_item_from_customer_db(int(update.message.from_user.id), item)
                msg = f"{item.capitalize()} successfully removed!"
                await context.bot.send_message(text=msg, chat_id=update.effective_chat.id)
            else:
                msg = f"{item.capitalize()} does not exist in your watchlist!"
                await context.bot.send_message(text=msg, chat_id=update.effective_chat.id)


async def unsubscribe_and_remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        logger.error("Error: effective_chat is None in unsubscribe_and_remove_command")
        return
    logger.info(f"Got remove all command from {update.effective_chat.id}")
    remove_customer_from_db(int(update.message.from_user.id))
    await context.bot.send_message(
        text="All items successfully removed!", chat_id=update.effective_chat.id
    )


# /list command
async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        logger.error("Error: effective_chat is None in list_command")
        return
    logger.info(f"Got list command from {update.effective_chat.id}")
    items = get_all_items_by_user_from_db(update.effective_chat.id)
    if items == None:
        await context.bot.send_message(
            text="You currently have no items added!\nYou can add some using the /add command.",
            chat_id=update.effective_chat.id,
        )
    else:
        msg = ""
        for item in items:
            logger.info(f"Item found: {item}")
            msg += item.capitalize() + "\n"
        msg_to_send = "Here is a list of your items:\n" + msg
        await context.bot.send_message(text=msg_to_send, chat_id=update.effective_chat.id)


# /update command
# TODO: Rework
async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        logger.error("Error: effective_chat is None in update_command")
        return
    logger.info(f"Got update command from {update.effective_chat.id}")
    list_of_updates = parse_update_message(update.effective_chat.id, update.message.text)
    update_values_in_customer_db(chat_id=update.effective_chat.id, updates=list_of_updates)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Your item specifications have been updated!"
    )


# Handler if command isn't recognized.
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        logger.error("Error: effective_chat is None in unknown_command")
        return
    logger.info(f"Got unknown command from {update.effective_chat.id}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command."
    )


async def invalid_medium(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        logger.error("Error: effective_chat is None in unknown_command")
        return
    logger.info(f"Got in valid medium from {update.effective_chat.id}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry, I can only handle text messages, not photos or videos.",
    )


# TODO: Make examples for each command.
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        logger.error("Error: effective_chat is None in help_command")
        return
    logger.info(f"Got help command from {update.effective_chat.id}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="""The following commands are available:
/start - Start the bot
/init - Initialize the bot
/add - Add an item to the watchlist
/remove - Remove an item from the watchlist
/list - List all items in the watchlist
/unsubscribe - Unsubscribe and remove all items from the watchlist""",
    )


# /error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat is None:
        logger.error("Error: effective_chat is None in error_handler")
        return
    logger.error(f"Got error from {update.effective_chat.id}")
    logger.error("Error:", context.error)
    traceback_str = "".join(
        traceback.format_exception(None, context.error, context.error.__traceback__)
    )
    logger.error(traceback_str)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry something went wrong!\nIf you need help, contact the developer or use the /help command.",
    )


# Method to send messages to specific chat_ids, without using a handler
async def send_notification(chat_id: int, msg: str, bot: telegram.Bot):
    logger.info(f"Sending notification to {chat_id}")
    await bot.send_message(
        chat_id=chat_id,
        text=msg,
    )
