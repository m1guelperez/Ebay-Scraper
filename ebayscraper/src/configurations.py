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
