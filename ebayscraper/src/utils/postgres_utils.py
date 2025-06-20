import contextlib
import psycopg2
import psycopg2.extensions
from ebayscraper.src.classes import Item, SearchRequest
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


# Used as initializing for the new users (/init command in telegram)
def add_user_to_db(chat_id: int) -> int:
    """
    Adds a new user to the database.
    If the user already exists, it does nothing.
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(
            f"""INSERT INTO {Tables.USERS} (chat_id)
               VALUES (%s)
               ON CONFLICT (chat_id) DO NOTHING;""",
            (chat_id,),
        )
        return cur.rowcount


def remove_user_from_db(chat_id: int):
    """
    Removes a user from the database based on chat_id.
    If the user does not exist, it does nothing.
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(
            f"""DELETE FROM {Tables.USERS} WHERE chat_id = (%s);""",
            (chat_id,),
        )
        res_of_sql_exc = cur.rowcount
    if res_of_sql_exc == 0:
        logger.info(f"No user with chat_id {chat_id} found in database.")
    else:
        logger.info(f"User with chat_id {chat_id} removed from database.")


def add_notification_sent_db(search_id: int, item_id: int):
    """
    Adds a notification sent record to the database.
    If the record already exists, it does nothing.
    This is used to prevent sending duplicate notifications for the same item.
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(
            f"""INSERT INTO {Tables.NOTIFICATIONS} (search_id, item_id)
            VALUES (%s, %s)
            ON CONFLICT (search_id, item_id) DO NOTHING;""",
            (
                search_id,
                item_id,
            ),
        )


def add_search_request_db(chat_id: int, search_request: SearchRequest) -> int:
    """
    Adds a search request to the database.
    If the search request already exists, it does nothing.
    """
    conflict_target = "(chat_id, item_name, item_price_limit, location, radius)"
    with get_db_cursor(commit=True) as cur:
        cur.execute(
            f"""INSERT INTO {Tables.SEARCHES} (chat_id, item_name, item_price_limit, location, radius)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT {conflict_target} DO NOTHING;""",
            (
                chat_id,
                search_request.item_name,
                search_request.price_limit,
                search_request.location,
                search_request.radius,
            ),
        )
        return cur.rowcount


def add_item_to_db(item: Item) -> int:
    """
    Adds an item to the database.
    If the item already exists, it updates the existing record.
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(
            f"""INSERT INTO {Tables.ITEMS} (ebay_identifier, item_name, price, url, last_seen_date)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (ebay_identifier) DO UPDATE SET
                price = EXCLUDED.price,
                last_seen_date = EXCLUDED.last_seen_date,
                item_name = EXCLUDED.item_name,
                url = EXCLUDED.url
            RETURNING item_id;""",
            (
                item.identifier,
                item.item_name,
                item.price,
                item.url,
                item.last_seen_date,
            ),
        )
        return cur.fetchone()[0]  # type: ignore # Will never be None, as we use RETURNING item_id


def remove_item_from_search_db(chat_id: int, item_name: str):
    """
    Removes a search request from the database based on chat_id and item_name.
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(
            f"""DELETE FROM {Tables.SEARCHES} WHERE chat_id = (%s) AND item_name = (%s);""",
            (
                chat_id,
                item_name,
            ),
        )


def remove_search_id_from_search_db(chat_id: int, search_id: int) -> SearchRequest | None:
    """
    Removes a search request from the database based on chat_id and search_id.
    """
    with get_db_cursor(commit=True) as cur:
        cur.execute(
            f"""DELETE FROM {Tables.SEARCHES} WHERE chat_id = (%s) AND search_id = (%s)
            RETURNING search_id, chat_id, item_name, item_price_limit, location, radius;""",
            (
                chat_id,
                search_id,
            ),
        )
        res_of_sql_exc = cur.fetchone()
    if res_of_sql_exc is None:
        return None
    else:
        return SearchRequest.from_db(res_of_sql_exc)


def get_item_via_name_from_db(chat_id: int, item_name: str) -> Item | None:
    """
    Retrieves an item from the database based on chat_id and item_name.
    If the item does not exist, it returns None.
    """
    with get_db_cursor() as cur:
        cur.execute(
            f"""SELECT item_id, ebay_identifier, item_name, price, url, last_seen_date FROM {Tables.ITEMS} WHERE chat_id = (%s) AND item_name = (%s);""",
            (chat_id, item_name),
        )
        res_of_sql_exc = cur.fetchone()
    if res_of_sql_exc is None:
        logger.info(f"Item with name {item_name} not found in database.")
        return None
    else:
        return Item.from_db(res_of_sql_exc)


def get_item_via_id_from_db(identifier: str) -> Item | None:
    """
    Retrieves an item from the database based on its ebay_identifier.
    If the item does not exist, it returns None."""
    with get_db_cursor() as cur:
        cur.execute(
            f"""SELECT item_id, ebay_identifier, item_name, price, url, last_seen_date FROM {Tables.ITEMS} WHERE ebay_identifier = (%s);""",
            (identifier,),
        )
        res_of_sql_exc = cur.fetchone()
    if res_of_sql_exc is None:
        logger.info(f"Item with identifier {identifier} not found in database.")
        return None
    else:
        return Item.from_db(res_of_sql_exc)


def check_if_notification_already_sent_db(search_id: int, item_id: int) -> bool:
    """
    Checks if a notification for a specific search_id and item_id has already been sent.
    Returns True if the notification has been sent, False otherwise."""
    with get_db_cursor() as cur:
        cur.execute(
            f"""SELECT 1 FROM {Tables.NOTIFICATIONS} WHERE search_id = (%s) AND item_id = (%s);""",
            (search_id, item_id),
        )
        res_of_sql_exc = cur.fetchone()
    if res_of_sql_exc is None:
        return False
    else:
        return True


def get_all_search_requests_by_user_from_db(chat_id: int) -> list[SearchRequest]:
    """
    Retrieves all search requests for a specific user based on chat_id.
    Returns a list of SearchRequest objects.
    If no search requests are found, it returns an empty list.
    """
    with get_db_cursor() as cur:
        cur.execute(
            f"""SELECT search_id, chat_id, item_name, item_price_limit, location, radius FROM {Tables.SEARCHES} WHERE chat_id = (%s);""",
            (chat_id,),
        )
        res_of_sql = cur.fetchall()
    return [SearchRequest.from_db(res) for res in res_of_sql]


def fetch_for_scraping() -> list[tuple]:
    """
    Fetches all the data from the search_criteria table in the database
    """
    with get_db_cursor() as cur:
        cur.execute(
            f"""SELECT search_id, 
                chat_id, 
                item_name, 
                item_price_limit, 
                location, 
                radius FROM {Tables.SEARCHES};"""
        )
        res_of_sql_exc = cur.fetchall()
    return res_of_sql_exc
