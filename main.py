import asyncio
import os
import urllib3
from dotenv import load_dotenv
from discord.ext import commands
from bs4 import BeautifulSoup
import sqlite3
import time
import logging


# LOGGING
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)


# BOT INITIALIZATION
load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
GUILD = os.getenv('DESTINATION_GUILD')
CHANNEL = os.getenv('DESTINATION_CHANNEL')
ROLE = os.getenv('NOTIFICATION_ROLE')
bot = commands.Bot(command_prefix='=> ', description="PS5 Tacker CH")
http = urllib3.PoolManager()
dbpath = os.path.abspath('./sources.db')


# FUNCTIONAL VARIABLES
bot.last_pinged = 0
bot.loop_time = 300
bot.running = False


# EVENTS
@bot.event
async def on_ready():
    if bot.running is False:
        console = bot.get_guild(int(GUILD)).get_channel(int(CHANNEL))
        await console.send('`SUCCESSFULLY JOINED CHANNEL`')
        await create_db(console)
        print(f'PS5 TRACKER OPERATIONAL')
        tracking_routine = asyncio.create_task(check_sites(console))
        await console.send(f'`STOCK CHECKER COMMENCING - INTERVAL AT {bot.loop_time} SECONDS`')
        bot.running = True
        await tracking_routine
    return


# COMMANDS
@bot.command(name='interval')
async def interval(ctx, interval):
    if ctx.author.id != 108305736131440640:
        await ctx.send('Command could not be executed since you are not ollie.', delete_afer=15)
        return
    await ctx.message.delete()
    bot.loop_time = int(interval)
    await ctx.send(f'Successfully changed loop interval to {interval} seconds.', delete_after=15)
    return


@bot.command(name='fixEntry')
async def fixEntry(ctx, title, toFix, content):
    if ctx.author.id != 108305736131440640:
        await ctx.send('Command could not be executed since you are not ollie.', delete_afer=15)
        return
    await ctx.message.delete()
    db = sqlite3.connect(dbpath)
    dbcursor = db.cursor()
    try:
        dbcursor.execute(f'UPDATE sources '
                     f'SET {toFix}="{content}"'
                     f'WHERE title="{title}";')
        await ctx.send(f'Successfully edited entry titled "`{title}`"', delete_after=15)
    except Exception as e:
        print(e)
        await ctx.send(f'Unexpected error when editing entry titled "`{title}`"', delete_after=15)
    dbcursor.close()
    db.commit()
    db.close()
    return


@bot.command(name='rmEntry')
async def rmEntry(ctx, title):
    if ctx.author.id != 108305736131440640:
        await ctx.send('Command could not be executed since you are not ollie.', delete_afer=15)
        return
    await ctx.message.delete()
    db = sqlite3.connect(dbpath)
    dbcursor = db.cursor()
    dbcursor.execute(f'DELETE FROM sources '
                     f'WHERE title="{title}";')
    dbcursor.close()
    db.commit()
    db.close()
    await ctx.send(f'Successfully deleted entry titled "`{title}`"', delete_after=15)
    return


@bot.command(name='addEntry')
async def rmEntry(ctx, title, url, selector, outOfStock):
    if ctx.author.id != 108305736131440640:
        await ctx.send('Command could not be executed since you are not ollie.', delete_afer=15)
        return
    await ctx.message.delete()
    db = sqlite3.connect(dbpath)
    dbcursor = db.cursor()
    dbcursor.execute(f'INSERT INTO sources '
                     f'(title, url, selector, outOfStock) '
                     f'VALUES ("{title}", "{url}", "{selector}", "{outOfStock}");')
    dbcursor.close()
    db.commit()
    db.close()
    await ctx.send(f'Successfully added entry titled "`{title}`"', delete_after=15)
    return


# CREATE DB IF NECESSARY
async def create_db(console):
    db = sqlite3.connect(dbpath)
    dbcursor = db.cursor()
    dbcursor.execute('CREATE TABLE IF NOT EXISTS sources('
                     'id INTEGER PRIMARY KEY,'
                     'title TEXT NOT NULL,'
                     'url TEXT NOT NULL,'
                     'selector TEXT NOT NULL,'
                     'outOfStock TEXT NOT NULL);')
    dbcursor.close()
    db.commit()
    db.close()
    await console.send('`INITIALIZED DB`')


# CHECK SITE
async def check_sites(console):
    while True:
        db = sqlite3.connect(dbpath)
        dbcursor = db.cursor()
        rows = dbcursor.execute('SELECT title, url, selector, outOfStock FROM sources')
        for row in rows:
            try:
                await check_site(console, row)
            except Exception as ex:
                await console.send(f'```html\n'
                                   f'{row[0]} | Response: -\n'
                                   f'REQUEST ERROR: {str(ex.__class__.__name__)}\n'
                                   f'<!-- {row[1]} -->```')
            await asyncio.sleep(1)
        dbcursor.close()
        db.close()
        await console.send(f'```asciidoc\n'
                           f'= LOOP FINISHED. CONTINUING AFTER {bot.loop_time} SECONDS. =```')
        await asyncio.sleep(bot.loop_time)


async def check_site(console, row):
    title = row[0]
    url = row[1]
    selector = row[2]
    outOfStock = row[3]
    header = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:86.0) Gecko/20100101 Firefox/86.0',
              'Accept': 'text/html',
              'Accept-Language': 'en-US'}
    try:
        r = http.request('GET', url=url, headers=header, timeout=urllib3.Timeout(connect=2.0, read=8.0), retries=False)
    except urllib3.exceptions.MaxRetryError:
        await console.send(f'```html\n'
                           f'{title} | Response: -\n'
                           f'REQUEST TIMED OUT\n'
                           f'<!-- {url} -->```')
        return
    status = r.status
    if str(status).startswith('2'):
        soup = BeautifulSoup(r.data, 'html.parser')
        try:
            current = str(soup.select(selector)[0])
        except Exception as e:
            print(e)
            current = 'ERROR WHEN READING WEBSITE'
        await console.send(f'```html\n'
                           f'{title} | Response: [{status}]\n'
                           f'{current}\n'
                           f'<!-- {url} -->```')
        if outOfStock not in current and time.time() - bot.last_pinged > 60*2:
            await console.send(f'<@&{ROLE}>')
            bot.last_pinged = time.time()
    else:
        await console.send(f'```html\n'
                           f'{title} | Response: [{status}]\n'
                           f'FAILED CHECK - GOOGLE THE HTTP RESPONSE CODE\n'
                           f'<!-- {url} -->```')
    return

bot.run(TOKEN)
