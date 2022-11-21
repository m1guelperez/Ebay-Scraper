from telegram.ext import ContextTypes
from telegram import Update
from scrape_async import *
import telegram
from configurations import TOKEN
from utilities.utils import parse_item_message, parse_update_message
from utilities.postgres_utils import (
    add_customer_values_to_db,
    user_exists_in_db,
    entry_in_customer_db_exists,
    remove_customer_values_from_db,
    get_all_items_by_user_from_db,
    update_values_in_customer_db,
)

# /start command
async def start_function(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
async def init_first_item(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
async def no_command_message(chat_id: int, context: ContextTypes.DEFAULT_TYPE):
    message = "Use some commands to get started!"
    await context.bot.send_message(text=message, chat_id=chat_id)


# /add command
async def add_item_to_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
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
async def remove_item_from_watchlist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    customer_values = parse_item_message(int(update.message.from_user.id), update.message.text)
    if entry_in_customer_db_exists(int(update.message.from_user.id), customer_values.item_name):
        remove_customer_values_from_db(int(update.message.from_user.id), customer_values.item_name)
        await context.bot.send_message(
            text="Item successfully removed!", chat_id=update.effective_chat.id
        )
    else:
        await context.bot.send_message(
            text="Item does not exist in your watchlist!", chat_id=update.effective_chat.id
        )


# /list command
async def list_items_of_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    items = get_all_items_by_user_from_db(update.effective_chat.id)
    if items == None:
        await context.bot.send_message(
            "You currently have no items added!\nYou can add some using the /add command."
        )
    else:
        msg = ""
        for item in items:
            msg += str(item[0] + "\n")
        await context.bot.send_message("Here is a list of your items:\n" + msg)


# /update command
# TODO: Test
async def update_item_attribs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    list_of_updates = parse_update_message(update.effective_chat.id, update.message.text)
    update_values_in_customer_db(chat_id=update.effective_chat.id, updates=list_of_updates)
    await context.bot.send_message(
        chat_id=update.effective_chat.id, text="Your item specifications have been updated!"
    )


# Handler if command isn't recognized.
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


# Method to send messages to specific chat_ids, without using a handler
async def send_notification(chat_id: int, msg: str):
    bot = telegram.Bot(token=TOKEN)
    await bot.send_message(
        chat_id=chat_id,
        text=msg,
    )
