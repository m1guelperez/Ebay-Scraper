import psycopg2
import psycopg2.extensions
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
    cur: psycopg2.extensions.cursor, connection: psycopg2.extensions.connection
):
    cur.close()
    connection.close()

connect_to_db()

def select_all_items_from_db():
    conn = connect_to_db()
    cur = conn.cursor()
    cur.execute("""SELECT * FROM items;""")
    res_of_sql_exc = cur.fetchall()
    print(res_of_sql_exc)
    close_db_connections(cur=cur, connection=conn)
    return res_of_sql_exc


select_all_items_from_db()