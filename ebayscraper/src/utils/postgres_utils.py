import contextlib
import psycopg2
import psycopg2.extensions
from datetime import datetime
from psycopg2.sql import SQL, Identifier
from ebayscraper.src.classes import Customer, ItemFromEbay
from ebayscraper.src.constants import DATABASE_PWD, PORT, USER, HOST, DATABASE, Tables
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


@contextlib.contextmanager
def get_db_cursor(commit=False):
    conn = None
    cursor = None
    try:
        conn = connect_to_db()
        cursor = conn.cursor()
        yield cursor  # Provide the cursor to the 'with' block
        if commit:
            conn.commit()
    except psycopg2.Error as e:
        logger.info(f"Database Error: {e}")
        if conn:
            conn.rollback()  # Rollback on error
        raise
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()  # Ensure connection is always closed


def connect_to_db() -> psycopg2.extensions.connection:
    conn = psycopg2.connect(
        database=DATABASE,
        user=USER,
        password=DATABASE_PWD,
        host=HOST,
        port=PORT,
    )
    return conn


def select_all_items_from_db() -> list[tuple]:
    with get_db_cursor() as cur:
        cur.execute(f"""SELECT * FROM {Tables.ITEMS};""")
        res_of_sql_exc = cur.fetchall()
    return res_of_sql_exc


# Used as initializing for the new customer (/init command in telegram)
def add_user_to_db(user_id: int):
    with get_db_cursor(commit=True) as cur:
        cur.execute(
            f"""INSERT INTO {Tables.USERS} (chat_id)
               VALUES (%s)
               ON CONFLICT (chat_id) DO NOTHING;""",
            (user_id,),
        )


def remove_customer_from_db(chat_id: int):
    with get_db_cursor(commit=True) as cur:
        cur.execute(
            f"""DELETE FROM {Tables.USERS} WHERE chat_id = (%s);""",
            (chat_id,),
        )


def add_notification_sent(chat_id: int, item_name: str):
    with get_db_cursor(commit=True) as cur:
        cur.execute(
            f"""UPDATE customer SET notification_sent = TRUE WHERE chat_id = (%s) AND item_name = (%s);""",
            (
                chat_id,
                item_name,
            ),
        )


def remove_item_from_customer_db(chat_id: int, item_name: str):
    with get_db_cursor(commit=True) as cur:
        cur.execute(
            """DELETE FROM customer WHERE chat_id = (%s) AND item_name = (%s);""",
            (
                chat_id,
                item_name,
            ),
        )


def entry_in_customer_db_exists(chat_id: int, item_name: str) -> bool:
    with get_db_cursor() as cur:
        cur.execute(
            """SELECT chat_id,item_name FROM customer WHERE chat_id = (%s) AND item_name = (%s);""",
            (
                chat_id,
                item_name,
            ),
        )
        res_of_sql_exc = cur.fetchone()
        if res_of_sql_exc == None:
            return False
        else:
            return True


def user_exists_in_db(chat_id: int) -> bool:
    with get_db_cursor() as cur:
        cur.execute(
            """SELECT chat_id FROM customer WHERE chat_id = (%s);""",
            (chat_id,),
        )
        res_of_sql_exc = cur.fetchone()
        if res_of_sql_exc == None:
            return False
        else:
            return True


def check_if_item_exists_in_db(identifier: str) -> bool:
    with get_db_cursor() as cur:
        cur.execute(
            """SELECT identifier FROM items WHERE identifier = (%s);""",
            (identifier,),
        )
        res_of_sql_exc = cur.fetchone()
        if res_of_sql_exc == None:
            return False
        else:
            return True


def add_item_to_db(item: ItemFromEbay):
    with get_db_cursor(commit=True) as cur:
        cur.execute(
            """INSERT INTO items (item_name,identifier,price,url,date)
            VALUES (%s,%s,%s,%s,%s);""",
            (item.item_name, item.identifier, item.price, item.url, item.date),
        )


def get_all_items_by_user_from_db(chat_id: int) -> list[str]:
    with get_db_cursor() as cur:
        cur.execute(
            """SELECT item_name FROM customer WHERE chat_id = (%s);""",
            (chat_id,),
        )
        res_of_sql = cur.fetchall()
    return [res[0] for res in res_of_sql]


# update[0] is the field we want to update in the database and update[1] the new value
# TODO: refactor, its really ugly
def update_values_in_customer_db(chat_id: int, updates: list):
    conn = connect_to_db()
    cur = conn.cursor()
    item_name = updates.pop(0)[1]
    update_field = ""
    for update in updates:
        if str(update[0]).lower() == "pricelimit":
            update_field = "item_price_limit"
        elif str(update[0]).lower() == "location":
            update_field = "location"
        elif str(update[0]).lower() == "radius":
            update_field = "radius"
        cur.execute(
            SQL(
                """UPDATE customer SET {column} = (%s) WHERE item_name = (%s) AND chat_id = (%s);"""
            ).format(
                column=Identifier(update_field),
            ),
            (
                update[1],
                item_name,
                chat_id,
            ),
        )
        conn.commit()
    conn.close()
    cur.close()


# Gets all the data from customer such that we can scrape it
# TODO: Change database format otherwise it could happen we scrape twice the same item, maybe join the chat_ids with the same characteristics
def fetch_for_scraping() -> list[tuple]:
    """
    Fetches all the data from the customer table in the database
    """
    with get_db_cursor() as cur:
        cur.execute("""SELECT * FROM customer;""")
        res_of_sql_exc = cur.fetchall()
    return res_of_sql_exc
