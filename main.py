import os
import json
import discord
import asyncio
import aiohttp
import logging
from colr import color
import pymongo
from rich.table import Table
from datetime import datetime
from rich.console import Console
from discord import app_commands
from discord.ext import commands
from rich.logging import RichHandler
from utils._checks import check_commands

if os.path.exists("config.json.example") and not os.path.exists("config.json"):
    print(color("Please rename the config.json.example to config.json and set your config options before continuing.", fore=(189, 16, 16)))
    os.abort()
if not os.path.exists("config.json"):
    print(color("Config is not found, please go to the github and look for the config exmaple.\nGithub: https://github.com/JonnyBoy2000/Fresh", fore=(189, 16, 16)))
    os.abort()
if not os.path.exists("./data/"):
    os.makedirs("./data/")
    os.makedirs('./data/logs')
with open("config.json", "r") as config:
    _config = json.load(config)

console = Console()
starttime = datetime.now()
logger = logging.getLogger()
logger.setLevel(logging.INFO)
dt_fmt = '%Y-%m-%d %H:%M:%S'
ch = RichHandler(level=logging.DEBUG, show_level=True)
ch.setLevel(logging.INFO)
ch.setFormatter(logging.Formatter('[{asctime}] {message}', dt_fmt, style='{'))
logger.addHandler(ch)
file_handler = logging.FileHandler(f'./data/logs/{datetime.now().date()}-commands.log')
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(logging.Formatter('[{asctime}] [{levelname}] {message}', dt_fmt, style='{'))
logger.addHandler(file_handler)

class Fresh(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned_or("f?"),
            pm_help=None,
            intents=discord.Intents.all(),
            tree_cls=app_commands.CommandTree
        )
        self.add_check(check_commands)
        self.logger = logger
        self.version = "v1.0.0"
        self.spotify_id = _config["spotify_id"]
        self.spotify_secret = _config["spotify_secret"]
        self.uptime = datetime.utcnow()
        self.colors = {
            "blue": (4, 95, 185),
            "cyan": (4, 211, 232),
            "purple": (123, 4, 232),
            "green": (4, 232, 95),
            "red": (189, 16, 16),
            "yellow": (163, 187, 3),
            "grey": (110, 108, 108)
        }

    async def clear_screen(self):
        if os.name == "nt":
            os.system("cls")
        else:
            os.system("clear")

    async def load_modules(self):
        modules_to_load = []
        modulestable = Table(style="blue")
        modulestable.add_column("Folder", style="cyan", justify="center")
        modulestable.add_column("Module", style="magenta", justify="center")
        modulestable.add_column("Enabled", justify="center", style="green")
        with console.status("Loading Fresh config and modules..") as status:
            await asyncio.sleep(0.5)
            status.update("Loading modules...")
            for key in _config['enabledModules']:
                if key == "jishaku":
                    name = "Jishaku"
                    folder = "Pip Cog"
                else:
                    name = key.split('.')[1].capitalize()
                    folder = str(key.split('.')[0])
                if _config['enabledModules'][key] == 1:
                    modules_to_load.append(key)
                    status.update(f"Loading {key}...")
                    try:
                        await self.load_extension(f"{key}")
                        modulestable.add_row(folder, name, "✔ True")
                    except Exception as e:
                        if isinstance(e, commands.ExtensionAlreadyLoaded):
                            pass
                        else:
                            console.print_exception(show_locals=False)
                        modulestable.add_row(folder, name, "❌ False")
                    await asyncio.sleep(0.5)
                else:
                    modulestable.add_row(folder, name, "❌ False")
        await self.clear_screen()
        return modulestable

    async def on_ready(self):
        await self.clear_screen()
        await asyncio.sleep(1)
        self.session = aiohttp.ClientSession()
        channels = len([c for c in self.get_all_channels()])
        login_time = datetime.now() - starttime
        login_time = login_time.seconds + login_time.microseconds / 1e6
        await self.change_presence(
            status=discord.Status.dnd,
            activity=discord.Activity(type=discord.ActivityType.watching, name=f"f?help | {len(self.guilds)} guilds..")
        )
        maintable = Table(style="blue")
        maintable.add_column("F.res.h", style="cyan", no_wrap=True)
        maintable.add_column("Developed By: Jonny#0181", style="magenta")
        maintable.add_row("Login time", f"{login_time} milliseconds.")
        maintable.add_row("Logged in as", f"{self.user.name} ({self.user.id})")
        maintable.add_row("Connected to", f"{len(self.guilds)} guilds and {channels} channels.")
        maintable.add_row("Python version", "{}.{}.{}".format(*os.sys.version_info[:3]))
        maintable.add_row("Discord.py version", f"{discord.__version__}")
        if _config["mongoURI"] != "Disabled.":            
            self.db = pymongo.MongoClient(_config["mongoURI"])
            self.db = self.db['testing']
            maintable.add_row("Database Status", 'Should be connected!')
        else:
            maintable.add_row("Database Status", "Disabled, not connecting.")
        modulestable = await self.load_modules()
        console.print(maintable, justify="left")
        console.print(modulestable)
        logger.warning("Attempting to sync application commands...")
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} commands globaly!")
        except Exception as e:
            logger.error(f"Failed to sync commands! Reason:\n{e}")

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
            print(f"Failed to login:\n{e}")

if __name__ == "__main__":
    Fresh().run()