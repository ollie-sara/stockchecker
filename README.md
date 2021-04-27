# stockchecker
Discord bot that simply checks the stock of an item on a website in a given interval.

---

## Starting The Bot
#### 1. Register a new bot on the [Discord Developer Portal](https://discord.com/developers/applications). Follow the instructions given on the site.
#### 2. Create and configure your .env file.
You need to configure it as follows:
```
DISCORD_TOKEN=<BOT TOKEN>
DESTINATION_GUILD=<SERVER ID>
DESTINATION_CHANNEL=<CHANNEL ID>
NOTIFICATION_ROLE=<ROLE ID>
```
The bot uses the destination channel as a sort of "console" and will constantly spam messages into it.
Make sure you use a seperate, dedicated tracking channel for this.
#### 3. Run the bot. This may be on your computer, but I would recommend something like a Raspberry Pi or a server.
---

## Usage

The bot centers around a "sources.db" sqlite3 database, which contains one table with all of the queries it will do.
It goes through each row, looking up the specified url and searching for the DOM element as given by a CSS selector that you supply.
It will then search the element for a string you supplied, and will notify you if it hasn't found the string, or if it hasn't found the element at all.

You use various commands with the prefix `=>` in Discord to edit the database (although you could technically do it with a database browser).

- `=> addEntry "<title>" "<url>" "<css selector>" "<string to search">` Adds an entry to the database. Will automatically be searched next run.
```
title: title of the entry (mediamarkt, digitec, newegg, etc.)
url: url that should be visited
css selector: the DOM element given by a css selector 
              (".availability .outOfStock", or similar)
string to search: string the stockchecker should look out for 
                  ("Stock currently not available", etc.)
```

- `=> rmEntry "<title">` Removes an entry from the database
```
title: title of the entry (mediamarkt, digitec, newegg, etc.)
```

- `=> fixEntry "<title>" {"url" || "selector" || "outOfStock"} "<fixed value>"` Edits an entry at a given column
```
title: title of the entry (mediamarkt, digitec, newegg, etc.)
second argument: any of the above mentioned. url and selector should be self-explanatory, 
                 outOfStock is equivalent to the "string to search".
fixed value: string to replace the old
```
- `=> interval <seconds>` Change checking interval to specified seconds. Default is 300 seconds (or 5min).
Setting this value too low will cause the bot to be ratelimited and eventually disconnected by discord. Experimentation wouldn't hurt.

---

This should include everything that you need to run the bot yourself.
