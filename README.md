# Ebay-Kleinanzeigen Scraper

This script notifies you if a new item of your choice has been published in a specific locatio while considering radius and pricelimit.
The notification will be send via telegram.

It uses a `Postgres` database to store the information persistent and make fast access available.

## Usage

### PostgreSQL

Install `PostgreSQL` on your machine and configure it to your needs.
Enter your credentials for the database in a `creds.toml` file in the root directory. the current tables are called `customer` and `items` and are hardcoded in the source code.

The customer table looks like that:

```SQL
CREATE TABLE customer (
    chat_id int,
    item_name VARCHAR(400),
    item_price_limit int,
    location VARCHAR(400),
    radius int
)
```

And the items table looks like that:

```SQL
CREATE TABLE items (
    item_name VARCHAR(400),
    identifier VARCHAR(400),
    price int,
    url VARCHAR(400),
    date TIMESTAMP
)
```

### Script

Create a new conda environment and use the following `pip install .` command. After that you can execute the `core.py` file and the script will run forever.

## TODOs

* [x] PostgreSQL integration
* [x] Use async
* [x] Replace channelbot with direct message bot
* [x] Use dev environment for testing new features
* [ ] Add conversation states for adding items
* [ ] Overhaul item procedure
* [ ] Write tests
