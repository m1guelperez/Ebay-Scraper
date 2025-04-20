from telegram.ext import ContextTypes
from telegram import Update
import traceback
import telegram
from ebayscraper.src.constants import TOKEN
from utils.utils import parse_item_message, parse_update_message, parse_remove_message
from constants import RADIUS
from utils.postgres_utils import (
    add_customer_values_to_db,
    user_exists_in_db,
    entry_in_customer_db_exists,
    remove_customer_values_from_db,
    get_all_items_by_user_from_db,
    update_values_in_customer_db,
)


# /start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Got start command from {update.effective_chat.id}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f"""Hello! This is the EbayAlerts bot.
        To get you started, please use the /init command and copy and fill the following message:
        The radius has to be one of the following values: {RADIUS}.
        For example like that:

        /init item, pricelimit, location, radius
        /init GTX 1080, 650, Köln, 20""",
    )


# /init command
async def init_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Got init command from {update.effective_chat.id}")
    customer_values = parse_item_message(int(update.message.from_user.id), update.message.text)
    if customer_values.radius not in RADIUS:
        await context.bot.send_message(
            text=f"The radius has to be: {RADIUS}!",
            chat_id=update.effective_chat.id,
        )
        return
    if not user_exists_in_db(int(update.message.from_user.id)):
        print(f"User does not exist in db, creating new user for {update.effective_chat.id}")
        add_customer_values_to_db(int(update.message.from_user.id), customer_values)
        print(f"Successfully added user {update.effective_chat.id} to db")
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
    print(f"Got no command message from {update.effective_chat.id}")
    message = "Use some commands to get started!"
    await context.bot.send_message(text=message, chat_id=update.effective_chat.id)


# /add command
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Got add command from {update.effective_chat.id}")
    customer_values = parse_item_message(int(update.message.from_user.id), update.message.text)
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
            text="Item successfully added!", chat_id=update.effective_chat.id
        )
    else:
        await context.bot.send_message(
            text="Item already exists in your watchlist!", chat_id=update.effective_chat.id
        )


# /remove command
async def remove_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Got remove command from {update.effective_chat.id}")
    items = parse_remove_message(update.message.text)
    if items == None:
        await context.bot.send_message(
            text="""Please use the following format:"
            /remove item1, item2, item3
            /remove GTX 1080, GTX 1070, GTX 1060""",
            chat_id=update.effective_chat.id,
        )
    else:
        for item in items:
            if entry_in_customer_db_exists(int(update.message.from_user.id), item):
                remove_customer_values_from_db(int(update.message.from_user.id), item)
                msg = str(item) + " successfully removed!"
                await context.bot.send_message(text=msg, chat_id=update.effective_chat.id)
            else:
                msg = str(item) + " does not exist in your watchlist!"
                await context.bot.send_message(text=msg, chat_id=update.effective_chat.id)


async def remove_all_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Got remove all command from {update.effective_chat.id}")
    remove_customer_values_from_db(int(update.message.from_user.id), None)
    await context.bot.send_message(
        text="All items successfully removed!", chat_id=update.effective_chat.id
    )


# /list command
async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Got list command from {update.effective_chat.id}")
    items = get_all_items_by_user_from_db(update.effective_chat.id)
    if items == None:
        await context.bot.send_message(
            "You currently have no items added!\nYou can add some using the /add command."
        )
    else:
        msg = ""
        for item in items:
            msg += str(item[0] + "\n")
        msg_to_send = "Here is a list of your items:\n" + msg
        await context.bot.send_message(text=msg_to_send, chat_id=update.effective_chat.id)


# /update command
# TODO: Test
async def update_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Got update command from {update.effective_chat.id}")
    list_of_updates = parse_update_message(update.effective_chat.id, update.message.text)
    update_values_in_customer_db(chat_id=update.effective_chat.id, updates=list_of_updates)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Your item specifications have been updated!"
    )


# Handler if command isn't recognized.
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Got unknown command from {update.effective_chat.id}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command."
    )


# TODO: Make examples for each command.
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"Got help command from {update.effective_chat.id}")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="""The following commands are available:
        /start - Start the bot
        /init - Initialize the bot
        /add - Add an item to the watchlist
        /remove - Remove an item from the watchlist
        /list - List all items in the watchlist
        /update - Update an item in the watchlist""",
    )


# /error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"Got error from {update.effective_chat.id}")
    print("Error:", context.error)
    traceback_str = "".join(
        traceback.format_exception(None, context.error, context.error.__traceback__)
    )
    print(traceback_str)
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry something went wrong!\nIf you need help, contact the developer or use the /help command.",
    )


# Method to send messages to specific chat_ids, without using a handler
async def send_notification(chat_id: int, msg: str):
    print(f"Sending notification to {chat_id}")
    bot = telegram.Bot(token=TOKEN)
    await bot.send_message(
        chat_id=chat_id,
        text=msg,
    )
