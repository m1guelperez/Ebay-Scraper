from telegram.ext import ContextTypes
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
import traceback
import telegram
from utils.utils import (
    parse_remove_search_query_message,
    extract_search_values,
)
from constants import RADIUS
from utils.postgres_utils import (
    add_user_to_db,
    remove_user_from_db,
    get_all_search_requests_by_user_from_db,
    remove_item_from_search_db,
    remove_search_id_from_search_db,
    add_search_request_db,
    get_search_via_name_from_db,
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
    rows_affected = add_user_to_db(
        int(update.message.from_user.id)
    )  # Add user to db the database handles the case if the user already exists.
    if rows_affected == 0:
        logger.info(f"The user {update.effective_chat.id} already exists in the db.")
    else:
        logger.info(f"Successfully added user {update.effective_chat.id} to db")
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
    search_values = extract_search_values(
        chat_message=update.message.text, chat_id=update.effective_chat.id
    )
    if search_values is None:
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
    if search_values.radius not in RADIUS:
        await context.bot.send_message(
            text=f"The radius has to be: {RADIUS}!",
            chat_id=update.effective_chat.id,
        )
        return
    rows_affected = add_search_request_db(
        int(update.message.from_user.id), search_values
    )  # The method handles the case if the user already exists in the db.
    if rows_affected == 0:
        logger.info(f"The search request for user {update.effective_chat.id} already exists.")
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
    logger.info(
        f"Successfully added search request from user with ID {update.effective_chat.id} to db"
    )
    await context.bot.send_message(
        text="Great search request was added!",
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
    search_values = extract_search_values(
        chat_message=update.message.text, chat_id=update.effective_chat.id
    )
    if search_values == None:
        await context.bot.send_message(
            text=(
                """Please use the following format:
"/add item, pricelimit, location, radius
"/add GTX 1080, 650, Köln, 20"""
            ),
            chat_id=update.effective_chat.id,
        )
        return
    if search_values.radius not in RADIUS:
        await context.bot.send_message(
            text=f"The radius has to be: {RADIUS}!",
            chat_id=update.effective_chat.id,
        )
        return
    rows_affected = add_search_request_db(
        int(update.message.from_user.id), search_values
    )  # The method handles the case if the search already exists in the db.
    if rows_affected != 0:
        logger.info(
            f"Successfully added search request from user with ID {update.effective_chat.id} to db"
        )
        await context.bot.send_message(
            text=f"'{search_values.item_name.capitalize()}' with a price limit of {search_values.price_limit}€ and a radius of {search_values.radius} km in {search_values.location.capitalize()} successfully added to your watchlist!",
            chat_id=update.effective_chat.id,
        )
    else:
        logger.info(f"The search request for user {update.effective_chat.id} already exists.")
        await context.bot.send_message(
            text=f"'{search_values.item_name.capitalize()}' with a price limit of {search_values.price_limit}€ and a radius of {search_values.radius} km in {search_values.location.capitalize()} already exists in your watchlist!\nIf you want to update it, please use the /update command.",
            chat_id=update.effective_chat.id,
        )


# /remove command
async def remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        logger.error("Error: effective_chat is None in remove_command")
        return
    logger.info(f"Got remove command from {update.effective_chat.id}")
    items = parse_remove_search_query_message(update.message.text)
    if not items:
        await context.bot.send_message(
            text="""Please use the following format:
/remove item1, item2, item3
/remove GTX 1080, GTX 1070, GTX 1060""",
            chat_id=update.effective_chat.id,
        )
    else:
        for item_name in items:
            if get_search_via_name_from_db(update.effective_chat.id, item_name):
                await remove_item_from_search_db(int(update.message.from_user.id), item_name)
                msg = f"{item_name.capitalize()} successfully removed!"
                await context.bot.send_message(text=msg, chat_id=update.effective_chat.id)
            else:
                msg = f"{item_name.capitalize()} does not exist in your watchlist!"
                await context.bot.send_message(text=msg, chat_id=update.effective_chat.id)


async def unsubscribe_and_remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        logger.error("Error: effective_chat is None in unsubscribe_and_remove_command")
        return
    logger.info(f"Got remove all command from {update.effective_chat.id}")
    await remove_user_from_db(int(update.message.from_user.id))
    await context.bot.send_message(
        text="All items successfully removed!", chat_id=update.effective_chat.id
    )


# /list command
async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat is None:
        logger.error("Error: effective_chat is None in list_command")
        return
    logger.info(f"Got list command from {update.effective_chat.id}")
    search_requests = await get_all_search_requests_by_user_from_db(update.effective_chat.id)

    if not search_requests:
        await context.bot.send_message(
            text="You have no search requests yet. Use /add to add a new search request.",
            chat_id=update.effective_chat.id,
        )
        return

    message_text = "Here is a list of your requests. Tap to delete:\n"
    keyboard = []  # This will be a list of lists of buttons

    for i, request in enumerate(search_requests):
        message_text += f"\n{i+1}. {request.item_name.capitalize()} für {request.price_limit}€ in {request.location.capitalize()} mit {request.radius}km Radius)\n"

        # Create a button for this item.
        # The callback_data is a string that the bot will receive when the button is pressed.
        button = InlineKeyboardButton(
            text=f"❌ Delete #{i+1}",
            callback_data=f"delete_search:{request.search_id}",  # e.g., "delete_search:5"
        )
        keyboard.append([button])  # Each button goes in its own list to appear on a new line

    reply_markup = InlineKeyboardMarkup(keyboard)

    await context.bot.send_message(
        text=message_text, chat_id=update.effective_chat.id, reply_markup=reply_markup
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


async def delete_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data:
        return
    await query.answer()

    # We know the action is "delete_search", we just need the ID
    search_id_str = query.data.split(":")[1]
    search_id_to_delete = int(search_id_str)

    res_of_sql = await remove_search_id_from_search_db(
        chat_id=int(query.from_user.id), search_id=search_id_to_delete
    )
    if res_of_sql is None:
        # await query.edit_message_text(text=f"❌ Search with ID {search_id_to_delete} not found.")
        logger.info(
            f"User {query.from_user.id} tried to delete non-existing search {search_id_to_delete}"
        )
        return
    await query.edit_message_text(text=f"✅ {res_of_sql.item_name.capitalize()} has been deleted.")
    logger.info(f"User {query.from_user.id} deleted item from search with ID {search_id_to_delete}")
