try:
    import os
    import json
    import discord
    import asyncio
    import aiohttp
    import logging
    from colr import color
    import pymongo
    import pathlib
    from rich.table import Table
    from datetime import datetime
    from discord import app_commands
    from discord.ext import commands
    from utils._checks import check_commands
    from logging.handlers import RotatingFileHandler
    from typing_extensions import Self
    from typing import Any
    from rich.console import Console
    from collections import deque
    from discord.utils import _ColourFormatter as ColourFormatter, stream_supports_colour
except ImportError:
    print("[ERROR] Missing dependency(s)! Please install required dependencies using the launcher.py script.")
    exit()

console = Console()
starttime = datetime.now()
logger = logging.getLogger(__name__)

if os.path.exists("config.json.example") and not os.path.exists("config.json"):
    print(color("Please rename the config.json.example to config.json and set your config options before continuing.", fore=(189, 16, 16)))
    os.abort()
if not os.path.exists("config.json"):
    print(color("Config is not found, please go to the github and look for the config exmaple.\nGithub: https://github.com/JonnyBoy2000/Fresh", fore=(189, 16, 16)))
    os.abort()
with open("config.json", "r") as config:
    _config = json.load(config)

class RemoveNoise(logging.Filter):
    def __init__(self):
        super().__init__(name="discord.state")

    def filter(self, record):
        if record.levelname == "WARNING" and "referencing an unknown" in record.msg:
            return False
        return True

class Logging:
    def __init__(self, *, stream: bool=True) -> None:
        self.log: logging.Logger = logging.getLogger()
        self.max_bytes: int = 32 * 1024 * 1024
        self.logging_path = pathlib.Path("./logs/")
        self.logging_path.mkdir(exist_ok=True)
        self.stream: bool = stream

    def __enter__(self: Self) -> Self:
        logging.getLogger("discord").setLevel(logging.INFO)
        logging.getLogger("discord.http").setLevel(logging.INFO)
        logging.getLogger("discord.http").setLevel(logging.INFO)
        logging.getLogger("discord.state").addFilter(RemoveNoise())

        self.log.setLevel(logging.INFO)
        handler = RotatingFileHandler(
            filename=self.logging_path / "Fresh.log", encoding="utf-8", mode="w", maxBytes=self.max_bytes, backupCount=5
        )
        dt_fmt = "%Y-%m-%d %H:%M:%S"
        fmt = logging.Formatter("[{asctime}] [{levelname:<7}] {name}: {message}", dt_fmt, style="{")
        handler.setFormatter(fmt)
        self.log.addHandler(handler)

        if self.stream:
            stream_handler = logging.StreamHandler()
            if stream_supports_colour(stream_handler):
                stream_handler.setFormatter(ColourFormatter())
            self.log.addHandler(stream_handler)

        return self

    def __exit__(self, *args: Any) -> None:
        handlers = self.log.handlers[:]
        for hdlr in handlers:
            hdlr.close()
            self.log.removeHandler(hdlr)


class Fresh(commands.Bot):
    def __init__(self) -> None:
        super().__init__(
            command_prefix=commands.when_mentioned_or(_config['prefix']),
            pm_help=None,
            intents=discord.Intents.all(),
            tree_cls=app_commands.CommandTree
        )
        self.add_check(check_commands)
        self.version = "v1.0.0"
        self.config = _config
        self.spotify_id = _config["spotify"]["id"]
        self.spotify_secret = _config["spotify"]["secret"]
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
        if _config["database"]["enabled"] != False:            
            collection = _config["database"]["collection"]
            self.db = pymongo.MongoClient(_config["database"]["uri"])[collection]
            maintable.add_row("Database Status", f'Connected to {collection}!')
        else:
            maintable.add_row("Database Status", "Disabled, not connecting.")
        modulestable = await self.load_modules()
        console.print(maintable, justify="left")
        console.print(modulestable)
        logger.info("Attempting to sync application commands...")
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} commands globaly!")
        except Exception as e:
            logger.exception(f"Failed to sync commands! Reason:\n{e}")

    async def send_sub_help(self, ctx, cmd):
        e = discord.Embed()
        e.colour = discord.Color.blurple()
        e.description = ""
        for c in cmd.commands:
            e.description += f"**{c.name}** - {c.short_doc}\n"
        e.set_thumbnail(url=self.user.avatar.url)
        e.set_author(name=f"Commands for {cmd.name}", icon_url=self.user.avatar.url)
        return await ctx.send(embed=e)

    #Let's try to add a fallback for the music channel when music is not enabled.
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.guild is None: return
        data = self.db.fresh_channel.find_one({"_id": message.guild.id})
        if data is not None:
            if message.channel.id == data['channel']:
                if self.get_cog('MusicChannel') is None or self.get_cog('Music') is None:
                    msg = await message.reply(
                        content="<:tickNo:697759586538749982> This music channel is currently disabled! It should be back up soon tho!")
                    await message.delete()
                    await asyncio.sleep(15)
                    await msg.delete()
        await self.process_commands(message)

    async def start(self) -> None:
        try:
            await super().start(token=_config['token'], reconnect=True)
        except Exception as e:
            logger.exception(e)

async def main():
    async with Fresh() as bot:
        session = aiohttp.ClientSession()
        bot.session = session
        with Logging():
            await bot.start()

if __name__ == "__main__":
    asyncio.run(main())