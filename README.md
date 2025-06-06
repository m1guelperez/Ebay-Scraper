# Ebay-Kleinanzeigen Scraper

This script notifies you if a new item of your choice has been published in a specific locatio while considering radius and pricelimit.
The notification will be send via telegram.

It uses a `Postgres` database to store the information persistent and make fast access possible.

## Usage

### Config file
Create a config file in the following format and place it into the root directory.
```JSON
{
    "scrape_url": "https://www.ebay-kleinanzeigen.de/s-",
    "radius": [
        5,
        10,
        20,
        30,
        50,
        100,
        150,
        200
    ],
    "token": "TOKEN",
    "postgres": {
        "user": "NAME",
        "password": "PASSWORD",
        "database": "DB_NAME",
        "host": "localhost",
        "port": 5432
    },
    "scrape_interval": 90
}
```

### PostgreSQL

Install `PostgreSQL` on your machine and configure it to your needs.
Enter your credentials for the database in a `creds.toml` file in the root directory. The current tables are called `users`, `search_criteria`, `items` and `notifications_sent` are hardcoded in the source code.

The `users` table looks like:

```SQL
CREATE TABLE users (
    chat_id BIGINT PRIMARY KEY,
    -- You could add other user-specific info here, like username, registration_date, etc.
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

The `search_criteria` table looks like:

```SQL
CREATE TABLE search_criteria (
    search_id SERIAL PRIMARY KEY, -- A unique ID for each search request
    chat_id BIGINT NOT NULL REFERENCES users(chat_id), -- Foreign key to users table
    item_name VARCHAR(400) NOT NULL, -- The user's search term
    item_price_limit INT,
    location VARCHAR(400),
    radius INT,
    is_active BOOLEAN DEFAULT TRUE, -- So users can pause/delete searches
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    CONSTRAINT uq_user_search UNIQUE NULLS NOT DISTINCT (chat_id, item_name, item_price_limit, location, radius)
);
```

The `items` table looks like:
```SQL
CREATE TABLE items (
    item_id SERIAL PRIMARY KEY, -- A unique internal ID for the item
    ebay_identifier VARCHAR(400) UNIQUE NOT NULL, -- The unique ID from eBay
    item_name VARCHAR(400), -- The actual name of the item from eBay
    price INT,
    url VARCHAR(400),
    scraped_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP, -- When this item was first scraped
    last_seen_date TIMESTAMP -- Optional: update if you re-scrape and find it again
);
```

The `notifications_sent` table looks like:
```SQL
CREATE TABLE notifications_sent (
    notification_id SERIAL PRIMARY KEY,
    search_id INT NOT NULL REFERENCES search_criteria(search_id),
    item_id INT NOT NULL REFERENCES items(item_id),
    notified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_search_item UNIQUE (search_id, item_id) -- Ensures a user is notified only once per item for a specific search
);
```

### Script

Create a new conda environment and use the following `pip install .` command. After that you can execute the `core.py` file and the script will run forever.

## TODOs

* [x] PostgreSQL integration
* [x] Use async
* [x] Replace channelbot with direct message bot
* [x] Use dev environment for testing new features
* [ ] Group scrapes for same requests by different users
* [ ] LLM into own process or async 
* [ ] Maybe convert some DB columns to indices
* [ ] Write tests
