import psycopg2
import psycopg2.extensions
from classes import Customer, ItemFromEbay
from configurations import DATABASE_PWD, PORT, USER, HOST, DATABASE


def connect_to_db() -> psycopg2.extensions.connection:
    conn = psycopg2.connect(
        database=DATABASE,
        user=USER,
        password=DATABASE_PWD,
        host=HOST,
        port=PORT,
    )
    return conn


def close_db_connections(
    cursor: psycopg2.extensions.cursor, connection: psycopg2.extensions.connection
):
    cursor.close()
    connection.close()


def select_all_items_from_db() -> list[tuple]:
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("""SELECT * FROM items;""")
    res_of_sql_exc = cur.fetchall()
    close_db_connections(cur=cur, connection=conn)
    return res_of_sql_exc


# Used as initializing for the new customer (/init command in telegram)
def add_new_customer_values(user_id: int, customer: Customer):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO customer (chat_id,item_name,item_price_limit,location,radius)
        VALUES (%s,%s,%s,%s,%s);""",
        (user_id, customer.item_name, customer.price_limit, customer.location, customer.radius),
    )
    conn.commit()
    close_db_connections(cursor=cur, connection=conn)


def remove_customer_values(user_id: int, customer: Customer):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute(
        """DELETE FROM customer WHERE chat_id = (%s) AND item_name = (%s);""",
        (user_id, customer.item_name, customer.price_limit, customer.location, customer.radius),
    )
    conn.commit()
    close_db_connections(cursor=cur, connection=conn)


def entry_in_customer_exists(chat_id: int, item_name: str) -> bool:
    conn = connect_to_db()
    cur = conn.cursor()
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
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("""SELECT chat_id FROM customer WHERE chat_id = (%s);""", (chat_id,))
    res_of_sql_exc = cur.fetchone()
    if res_of_sql_exc == None:
        return False
    else:
        return True


def check_if_item_exists_in_db(identifier: str) -> bool:
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("""SELECT identifier FROM items WHERE identifier = (%s);""", (identifier,))
    res_of_sql_exc = cur.fetchone()
    if res_of_sql_exc == None:
        return False
    else:
        return True


def add_item_to_db(item: ItemFromEbay):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute(
        """INSERT INTO items (item_name,identifier,price,url,date)
        VALUES (%s,%s,%s,%s,%s);""",
        (item.item_name, item.identifier, item.price, item.url, item.date),
    )
    conn.commit()
    close_db_connections(cursor=cur, connection=conn)


def get_all_items_by_user(chat_id: int):
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("""SELECT item_name FROM customer WHERE chat_id = (%s);""", (chat_id,))
    res_of_sql = cur.fetchall()
    close_db_connections(cursor=cur, connection=conn)
    return res_of_sql


# Gets all the data from customer such that we can scrape it
# TODO: Change database format otherwise it could happen we scrape twice the same item, maybe join the chat_ids with the same characteristics
def fetch_for_scraping() -> list[tuple]:
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("""SELECT * FROM customer;""")
    res_of_sql_exc = cur.fetchall()
    close_db_connections(cursor=cur, connection=conn)
    return res_of_sql_exc
