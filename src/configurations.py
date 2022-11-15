from utils import load_configfile

TOKEN = load_configfile("./creds.toml")["telegram"]["token"]
CHANNEL_ID = load_configfile("./creds.toml")["telegram"]["channelID"]
DATABASE_PWD = load_configfile("./creds.toml")["postgres"]["password"]
DATABASE = load_configfile("./creds.toml")["postgres"]["dbName"]
HOST = load_configfile("./creds.toml")["postgres"]["host"]
USER = load_configfile("./creds.toml")["postgres"]["user"]
PORT = load_configfile("./creds.toml")["postgres"]["port"]
