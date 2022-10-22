import requests
from bs4 import BeautifulSoup
import re
import datetime

from utils import connect_to_db

# Scrapes ebay for a particular item and a custom radius and location
def scrape(pwd: str, item: str) -> int:
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.47"
    }
    ebay_request = requests.get(
        "https://www.ebay-kleinanzeigen.de/s-juechen/" + item + "/k0l1185r100",
        headers=header,
    )

    soup = BeautifulSoup(ebay_request.content, "html.parser")
    conn = connect_to_db(pwd)
    cur = conn.cursor()
    counter = 0
    # a is the tag
    for entry in soup.find_all("a", href=re.compile("/s-anzeige/(.*)" + item + "(.*)")):
        cur.execute("""SELECT title FROM items WHERE title = (%s);""", (entry["href"],))
        res_of_sql_exc = cur.fetchone()
        if res_of_sql_exc == None:
            cur = conn.cursor()
            cur.execute(
                """INSERT INTO items(title,date_of_input)
                VALUES (%s,%s);""",
                (
                    entry["href"],
                    datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                ),
            )
            counter = counter + 1
    conn.commit()
    conn.close()
    return counter
