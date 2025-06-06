import json
from pathlib import Path


def load_configfile(path: str) -> dict:
    return json.load(open(Path(path).resolve(), "r"))


loaded_file = load_configfile("./config.json")
TOKEN = loaded_file["token"]
DATABASE_PWD = loaded_file["postgres"]["password"]
DATABASE = loaded_file["postgres"]["database"]
HOST = loaded_file["postgres"]["host"]
USER = loaded_file["postgres"]["user"]
PORT = loaded_file["postgres"]["port"]
SCRAPE_URL = loaded_file["scrape_url"]
RADIUS = loaded_file["radius"]
SCRAPE_INTERVAL = loaded_file["scrape_interval"]


class Tables:
    USERS = loaded_file["tables"]["users"]
    ITEMS = loaded_file["tables"]["items"]
    NOTIFICATIONS = loaded_file["tables"]["notifications"]
    SEARCHES = loaded_file["tables"]["searches"]
