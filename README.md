# Ebay-Kleinanzeigen Scraper

This script notifies you if a new item of your choice has been published in a specific radius and location.
The notification will be send via telegram.

It uses a `Postgres` database to store the information persistent and make fast access available.

## Usage

Enter your credentials for the database in a `creds.toml` file and the add all the items you want to look for into the `items.toml` file. Then place them in the root directory.
