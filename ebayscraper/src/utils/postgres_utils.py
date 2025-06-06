import contextlib
from psycopg import sql
from psycopg_pool import AsyncConnectionPool
from ebayscraper.src.classes import Item, SearchRequest
from ebayscraper.src.constants import DATABASE_PWD, PORT, USER, HOST, DATABASE, Tables
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

conn_string = f"dbname={DATABASE} user={USER} password={DATABASE_PWD} host={HOST} port={PORT}"
async_pool = AsyncConnectionPool(open=False, max_size=15, conninfo=conn_string)


@contextlib.asynccontextmanager
async def get_db_cursor(commit=False):
    async with async_pool.connection() as aconn:
        async with aconn.cursor() as acur:
            try:
                yield acur
                if commit:
                    await aconn.commit()
            except Exception:
                await aconn.rollback()
                raise
            finally:
                await acur.close()


# Used as initializing for the new users (/init command in telegram)
async def add_user_to_db(chat_id: int) -> int:
    """
    Adds a new user to the database.
    If the user already exists, it does nothing.
    """
    query_template = sql.SQL(
        """INSERT INTO {} ({field})
           VALUES ({placeholder})
           ON CONFLICT ({conflict_field}) DO NOTHING;"""
    )
    field = sql.Identifier("chat_id")
    placeholder = sql.Placeholder()
    conflict_field = field
    finished_query = query_template.format(
        table=sql.Identifier(Tables.USERS),
        field=field,
        conflict_field=conflict_field,
        placeholder=placeholder,
    )

    async with get_db_cursor(commit=True) as acur:
        await acur.execute(
            finished_query,
            (chat_id,),
        )
        return acur.rowcount


async def remove_user_from_db(chat_id: int):
    """
    Removes a user from the database based on chat_id.
    If the user does not exist, it does nothing.
    """
    query_template = sql.SQL("""DELETE FROM {table} WHERE chat_id = {field};""")
    table_name = sql.Identifier(Tables.USERS)
    field = sql.Identifier("chat_id")
    finished_query = query_template.format(
        table=table_name,
        field=field,
    )

    async with get_db_cursor(commit=True) as acur:
        await acur.execute(
            finished_query,
            (chat_id,),
        )
        res_of_sql_exc = acur.rowcount
    if res_of_sql_exc == 0:
        logger.info(f"No user with chat_id {chat_id} found in database.")
    else:
        logger.info(f"User with chat_id {chat_id} removed from database.")


async def add_notification_sent_db(search_id: int, item_id: int):
    """
    Adds a notification sent record to the database.
    If the record already exists, it does nothing.
    This is used to prevent sending duplicate notifications for the same item.
    """
    query_template = sql.SQL(
        """INSERT INTO {table} ({fields})
              VALUES ({placeholders})
              ON CONFLICT ({conflict_fields}) DO NOTHING;"""
    )
    table_name = sql.Identifier(Tables.NOTIFICATIONS)
    columns = [
        sql.Identifier("search_id"),
        sql.Identifier("item_id"),
    ]
    fields_sql = sql.SQL(",").join(columns)
    placeholders = sql.SQL(",").join(sql.Placeholder() * len(columns))
    conflict_fields = fields_sql

    finished_query = query_template.format(
        table=table_name,
        fields=fields_sql,
        placeholders=placeholders,
        conflict_fields=conflict_fields,
    )

    async with get_db_cursor(commit=True) as acur:
        await acur.execute(
            finished_query,
            (
                search_id,
                item_id,
            ),
        )


async def add_search_request_db(chat_id: int, search_request: SearchRequest) -> int:
    """
    Adds a search request to the database.
    If the search request already exists, it does nothing.
    """
    query_template = sql.SQL(
        """
        INSERT INTO {table} ({fields})
        VALUES ({placeholders})
        ON CONFLICT ({conflict_fields}) DO NOTHING
    """
    )

    # Define the identifiers (table and column names) using sql.Identifier
    #    This tells psycopg these are safe and should be quoted.
    table_name = sql.Identifier(Tables.SEARCHES)
    columns = [
        sql.Identifier("chat_id"),
        sql.Identifier("item_name"),
        sql.Identifier("item_price_limit"),
        sql.Identifier("location"),
        sql.Identifier("radius"),
    ]

    # Create a list of the fields as a comma-separated SQL object
    fields_sql = sql.SQL(",").join(columns)

    # Create the list of value placeholders (%s) dynamically
    placeholders_sql = sql.SQL(",").join(sql.Placeholder() * len(columns))

    composed_query = query_template.format(
        table=table_name,
        fields=fields_sql,
        placeholders=placeholders_sql,
        conflict_fields=fields_sql,
    )
    async with get_db_cursor(commit=True) as acur:
        await acur.execute(
            composed_query,
            (
                chat_id,
                search_request.item_name,
                search_request.price_limit,
                search_request.location,
                search_request.radius,
            ),
        )
        return acur.rowcount


async def add_item_to_db(item: Item) -> int:
    """
    Adds an item to the database.
    If the item already exists, it updates the existing record.
    """
    query_template = sql.SQL(
        """
        INSERT INTO {table} ({fields})
        VALUES ({placeholders})
        ON CONFLICT ({conflict_fields}) DO UPDATE SET
            price = EXCLUDED.price,
            last_seen_date = EXCLUDED.last_seen_date,
            item_name = EXCLUDED.item_name,
            url = EXCLUDED.url
        RETURNING item_id;
    """
    )
    table_name = sql.Identifier(Tables.ITEMS)
    columns = [
        sql.Identifier("ebay_identifier"),
        sql.Identifier("item_name"),
        sql.Identifier("price"),
        sql.Identifier("url"),
        sql.Identifier("last_seen_date"),
    ]
    fields_sql = sql.SQL(",").join(columns)
    placeholders_sql = sql.SQL(",").join(sql.Placeholder() * len(columns))
    conflict_fields = sql.Identifier("ebay_identifier")
    composed_query = query_template.format(
        table=table_name,
        fields=fields_sql,
        placeholders=placeholders_sql,
        conflict_fields=conflict_fields,
    )

    async with get_db_cursor(commit=True) as acur:
        await acur.execute(
            composed_query,
            (
                item.identifier,
                item.item_name,
                item.price,
                item.url,
                item.last_seen_date,
            ),
        )
        return (await acur.fetchone())[0]  # type: ignore # Will never be None, as we use RETURNING item_id. We have to await first thus the parantheses here.


async def remove_item_from_search_db(chat_id: int, item_name: str) -> None:
    """
    Removes a search request from the database based on chat_id and item_name.
    """
    query_template = sql.SQL(
        """
        DELETE FROM {table} 
        WHERE chat_id = %s AND item_name = %s;
    """
    )
    table_identifier = sql.Identifier(Tables.SEARCHES)
    composed_query = query_template.format(table=table_identifier)

    async with get_db_cursor(commit=True) as acur:
        await acur.execute(
            composed_query,
            (
                chat_id,
                item_name,
            ),
        )


async def remove_search_id_from_search_db(chat_id: int, search_id: int) -> SearchRequest | None:
    """
    Deletes a search request from the database based on chat_id and search_id
    and returns the deleted row.
    """
    query_template = sql.SQL(
        """
        DELETE FROM {table} 
        WHERE chat_id = %s AND search_id = %s
        RETURNING search_id, chat_id, item_name, item_price_limit, location, radius;
    """
    )

    table_identifier = sql.Identifier(Tables.SEARCHES)
    composed_query = query_template.format(table=table_identifier)

    async with get_db_cursor(commit=True) as acur:
        await acur.execute(
            composed_query,
            (
                chat_id,
                search_id,
            ),
        )
        deleted_row_tuple = await acur.fetchone()

    if deleted_row_tuple is None:
        return None
    else:
        return SearchRequest.from_db(deleted_row_tuple)


async def get_search_via_name_from_db(chat_id: int, item_name: str) -> SearchRequest | None:
    """
    Retrieves a user's search request from the database based on chat_id and item_name.
    """
    query_template = sql.SQL(
        """
        SELECT search_id, chat_id, item_name, item_price_limit, location, radius 
        FROM {table} 
        WHERE chat_id = %s AND item_name = %s; 
    """
    )
    table_identifier = sql.Identifier(Tables.SEARCHES)
    composed_query = query_template.format(table=table_identifier)

    async with get_db_cursor() as acur:
        await acur.execute(composed_query, (chat_id, item_name))
        res_of_sql_exc = await acur.fetchone()

    if res_of_sql_exc is None:
        logger.info(f"Search request '{item_name}' for user {chat_id} not found in database.")
        return None
    else:
        return SearchRequest.from_db(res_of_sql_exc)


async def get_item_via_id_from_db(identifier: str) -> Item | None:
    """
    Retrieves an item from the database based on its ebay_identifier.
    If the item does not exist, it returns None.
    """
    query_template = sql.SQL(
        """
        SELECT item_id, ebay_identifier, item_name, price, url, last_seen_date
        FROM {table} 
        WHERE ebay_identifier = %s;
    """
    )
    table_identifier = sql.Identifier(Tables.ITEMS)
    composed_query = query_template.format(table=table_identifier)

    async with get_db_cursor() as acur:
        await acur.execute(composed_query, (identifier,))
        res_of_sql_exc = await acur.fetchone()

    if res_of_sql_exc is None:
        logger.info(f"Item with identifier {identifier} not found in database.")
        return None
    else:
        return Item.from_db(res_of_sql_exc)


async def check_if_notification_already_sent_db(search_id: int, item_id: int) -> bool:
    """
    Checks if a notification for a specific search_id and item_id has already been sent.
    Returns True if the notification has been sent, False otherwise.
    """
    query_template = sql.SQL(
        """
        SELECT 1 FROM {table} 
        WHERE search_id = %s AND item_id = %s;
    """
    )
    table_identifier = sql.Identifier(Tables.NOTIFICATIONS)
    composed_query = query_template.format(table=table_identifier)

    async with get_db_cursor() as acur:
        await acur.execute(composed_query, (search_id, item_id))
        res_of_sql_exc = await acur.fetchone()
    # If fetchone() returns a row, it's "truthy". If it returns None, it's "falsy".
    return bool(res_of_sql_exc)


async def get_all_search_requests_by_user_from_db(chat_id: int) -> list[SearchRequest]:
    """
    Retrieves all search requests for a specific user based on chat_id
    Returns a list of SearchRequest objects.
    """
    query_template = sql.SQL(
        """
        SELECT search_id, chat_id, item_name, item_price_limit, location, radius 
        FROM {table} 
        WHERE chat_id = %s;
    """
    )
    table_identifier = sql.Identifier(Tables.SEARCHES)
    composed_query = query_template.format(table=table_identifier)

    async with get_db_cursor() as acur:
        await acur.execute(composed_query, (chat_id,))
        res_of_sql_exc = await acur.fetchall()
    return [SearchRequest.from_db(res_tuple) for res_tuple in res_of_sql_exc]


async def fetch_for_scraping() -> list[tuple]:
    """
    Fetches all active search requests from the database
    """
    query_template = sql.SQL(
        """
        SELECT 
            search_id, 
            chat_id, 
            item_name, 
            item_price_limit, 
            location, 
            radius 
        FROM {table}
        WHERE is_active = TRUE;
    """
    )
    table_identifier = sql.Identifier(Tables.SEARCHES)
    composed_query = query_template.format(table=table_identifier)

    async with get_db_cursor() as acur:
        await acur.execute(composed_query)
        res_of_sql_exc = await acur.fetchall()
    return res_of_sql_exc
