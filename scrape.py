import requests
from bs4 import BeautifulSoup
import re

from constants import RTX_3080


def scrape(item: str):
    header = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/106.0.0.0 Safari/537.36 Edg/106.0.1370.47"
    }
    ebay_request = requests.get(
        "https://www.ebay-kleinanzeigen.de/s-juechen/rtx-3080/k0l1185r100",
        headers=header,
    )

    soup = BeautifulSoup(ebay_request.content, "html.parser")
    res_list = []
    # a is the tag
    for entry in soup.find_all("a", href=re.compile("/s-anzeige/(.*)" + item + "(.*)")):
        print("Found the URL:", entry["href"])
        # use something with a hash
        if entry["href"] not in res_list:
            res_list.append(str(entry["href"])[11:])
    print("List: " + str(res_list))


scrape(RTX_3080)
