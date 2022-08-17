import discord
import os
import json
import aiohttp
import datetime
import logging
import asyncio
import aiosqlite
from colr import color
from discord.ext import commands
from utils._checks import check_commands
from rich.logging import RichHandler
from motor.motor_asyncio import AsyncIOMotorClient
from rich.console import Console
from rich.table import Table

console = Console()
starttime = datetime.datetime.now()

logger = logging.getLogger()
logger.setLevel(logging.INFO)
ch = RichHandler(level=logging.DEBUG, show_level=True)
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', '%Y-%m-%d %H:%M'))
logger.addHandler(ch)
file_handler = logging.FileHandler('./data/commands.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('%(asctime)s | %(levelname)s | %(message)s', '%Y-%m-%d %H:%M'))
logger.addHandler(file_handler)

if os.path.exists("config.json.example") and not os.path.exists("config.json"):
    print(color("Please rename the config.json.example to config.json and set your config options before continuing.", fore=(189, 16, 16)))
    os.abort()
if not os.path.exists("config.json"):
    print(color("Config is not found, please go to the github and look for the config exmaple.\nGithub: https://github.com/JonnyBoy2000/Fresh", fore=(189, 16, 16)))
    os.abort()
if not os.path.exists("./data/"):
    os.makedirs("./data/")
with open("config.json", "r") as config:
    _config = json.load(config)

class Fresh(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or(self.get_prefix),
            description="",
            pm_help=None,
            case_insensitive=True,
            intents=discord.Intents.all(),
        )
        self.logger = logger
        self.version = "v1.0.0"
        self.spotify_id = _config["spotify_id"]
        self.spotify_secret = _config["spotify_secret"]
        self.stats = {}
        self.sniped = []
        self.uptime = datetime.datetime.utcnow()
        self.add_check(check_commands)
        self.colors = {
            "blue": (4, 95, 185),
            "cyan": (4, 211, 232),
            "purple": (123, 4, 232),
            "green": (4, 232, 95),
            "red": (189, 16, 16),
            "yellow": (163, 187, 3),
            "grey": (110, 108, 108)
        }

    async def get_prefix(bot, message):
        async with aiosqlite.connect("./data/prefixes.db") as db:
            getData = await db.execute("SELECT * FROM prefixs WHERE guild = ?", (message.guild.id,))
            data = await getData.fetchone()
            if data is None:
                return _config["prefix"]
            else:
                return data[0]

    async def clear_screen(self):
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")

    async def load_modules(self):
        modules_to_load = []
        with console.status("Loading Fresh config and modules..") as status:
            await asyncio.sleep(0.5)
            status.update("Loading config...")
            for key in _config['enabledModules']:
                if _config['enabledModules'][key] == 1:
                    modules_to_load.append(key)
            await asyncio.sleep(0.5)
            status.update("Loading modules...")
            await asyncio.sleep(0.5)
            for stat in modules_to_load:
                status.update(f"Loading {stat}...")
                try:
                    await self.load_extension(f"{stat}")
                except Exception as e:
                    if isinstance(e, commands.ExtensionAlreadyLoaded):
                        pass
                    else:
                        console.print_exception(show_locals=False)
                await asyncio.sleep(0.5)
        await self.clear_screen()

    async def on_ready(self):
        await self.clear_screen()
        await asyncio.sleep(1)
        self.session = aiohttp.ClientSession()
        channels = len([c for c in self.get_all_channels()])
        login_time = datetime.datetime.now() - starttime
        login_time = login_time.seconds + login_time.microseconds / 1e6
        maintable = Table(style="blue")
        maintable.add_column("F.res.h", style="cyan", no_wrap=True)
        maintable.add_column("Developed By: Jonny#0181", style="magenta")
        maintable.add_row("Login time", f"{login_time} milliseconds.")
        maintable.add_row("Logged in as", f"{self.user.name} ({self.user.id})")
        maintable.add_row("Connected to", f"{len(self.guilds)} guilds and {channels} channels.")
        maintable.add_row("Python version", "{}.{}.{}".format(*os.sys.version_info[:3]))
        maintable.add_row("Discord.py version", f"{discord.__version__}")
        await self.change_presence(
            status=discord.Status.dnd,
            activity=discord.Activity(
                type=discord.ActivityType.watching,
                name=f"f?help | {len(self.guilds)} guilds.."
            )
        )
        if _config["mongoURI"] != "Disabled.":
            self.db = AsyncIOMotorClient(_config["mongoURI"])["db"]
            maintable.add_row("Database Status", 'Should be connected!')
        else:
            maintable.add_row("Database Status", "Disabled, not connecting.")
        await self.load_modules()
        modulestable = Table(style="blue")
        loadedmodules = [c.__module__ for c in self.cogs.values()]
        modulestable.add_column("Folder", style="cyan", justify="center")
        modulestable.add_column("Module", style="magenta", justify="center")
        modulestable.add_column("Loaded", justify="center", style="green")
        for key in _config['enabledModules']:
            if key != "jishaku":
                name = key.split('.')[1]
                folder = str(key.split('.')[0]).capitalize()
            else:
                name = "Jishaku"
                folder = "Pip Cog"
            if key in loadedmodules:
                modulestable.add_row(folder, name, "✔ True")
            else:
                modulestable.add_row(folder, name, "❌ False")
        console.print(maintable, justify="left")
        console.print(modulestable)
        logger.warning("Attempting to sync application commands...")
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} commands globaly!")
        except Exception as e:
            logger.error(f"Failed to sync commands! Reason:\n{e}")

    async def on_command_completion(self, ctx):
        command = ctx.command.name
        author = ctx.author
        guild = ctx.guild
        logger.info(f"Command {command} | Ran by {author.name} ({author.id}) in guild {guild.name}")

    async def send_sub_help(self, ctx, cmd):
        e = discord.Embed()
        e.colour = discord.Color.blurple()
        e.description = ""
        for c in cmd.commands:
            e.description += f"**{c.name}** - {c.short_doc}\n"
        e.set_thumbnail(url=self.user.avatar.url)
        e.set_author(name=f"Commands for {cmd.name}", icon_url=self.user.avatar.url)
        return await ctx.send(embed=e)

    def run(self):
        try:
            super().run(_config["token"])
        except Exception as e:
            print(color(f"Failed to login:\n{e}", fore=self.colors["red"]))

if __name__ == "__main__":
    Fresh().run()
