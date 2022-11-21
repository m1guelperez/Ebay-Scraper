from telegram.ext import ContextTypes
from telegram import Update
from scrape_async import *
import telegram
from configurations import TOKEN
from utilities.utils import parse_item_message, parse_update_message, parse_remove_message
from utilities.postgres_utils import (
    add_customer_values_to_db,
    user_exists_in_db,
    entry_in_customer_db_exists,
    remove_customer_values_from_db,
    get_all_items_by_user_from_db,
    update_values_in_customer_db,
)

# /start command
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Got start command")
    await context.bot.send_message(
        text="Hello! This is the EbayAlerts bot.\nTo get you started, please use the /init command and copy and fill the following message:\n"
        + "For example like that:",
        chat_id=update.effective_chat.id,
    )
    await context.bot.send_message(
        text="/init\n"
        + "Item: Gtx 1080\n"
        + "Pricelimit: 200 \n"
        + "Location: Köln\n"
        + "Radius (in km): 20",
        chat_id=update.effective_chat.id,
    )


# /init command
async def init_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Got init command")
    if not user_exists_in_db(int(update.message.from_user.id)):
        customer_values = parse_item_message(int(update.message.from_user.id), update.message.text)
        add_customer_values_to_db(int(update.message.from_user.id), customer_values)
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


# for everything different then a command
async def no_command_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Got no command message")
    message = "Use some commands to get started!"
    await context.bot.send_message(text=message, chat_id=update.effective_chat.id)


# /add command
async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Got add command")
    customer_values = parse_item_message(int(update.message.from_user.id), update.message.text)
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
    print("Got remove command")
    item_name = parse_remove_message(int(update.message.from_user.id), update.message.text)
    if entry_in_customer_db_exists(int(update.message.from_user.id), item_name):
        remove_customer_values_from_db(int(update.message.from_user.id), item_name)
        await context.bot.send_message(
            text="Item successfully removed!", chat_id=update.effective_chat.id
        )
    else:
        await context.bot.send_message(
            text="Item does not exist in your watchlist!", chat_id=update.effective_chat.id
        )


# /list command
async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Got list command")
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
    print("Got update command")
    list_of_updates = parse_update_message(update.effective_chat.id, update.message.text)
    update_values_in_customer_db(chat_id=update.effective_chat.id, updates=list_of_updates)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Your item specifications have been updated!"
    )


# Handler if command isn't recognized.
async def unknown_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Got unknown command")
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Sorry, I didn't understand that command."
    )


# TODO: Make examples for each command.
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("Got help command")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="The following commands are available:\n"
        + "/start - Start the bot\n"
        + "/init - Initialize the bot\n"
        + "/add - Add an item to the watchlist\n"
        + "/remove - Remove an item from the watchlist",
    )


# /error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("Got error")
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text="Sorry something went wrong!\nIf you need help, contact the developer or use the /help command.",
    )


# Method to send messages to specific chat_ids, without using a handler
async def send_notification(chat_id: int, msg: str):
    bot = telegram.Bot(token=TOKEN)
    await bot.send_message(
        chat_id=chat_id,
        text=msg,
    )
