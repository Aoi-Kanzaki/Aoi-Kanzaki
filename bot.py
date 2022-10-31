import os
import json
import discord
import pymongo
import aiohttp
import asyncio
from datetime import datetime
from discord.ext import commands

from rich.console import Console as RichConsole
richConsole = RichConsole()

with open("config.json", "r") as config:
    _config = json.load(config)


class Fresh(commands.AutoShardedBot):
    def __init__(self, **options):
        super().__init__(**options)
        self.started = datetime.utcnow()
        self._init = False
        self.config = _config
        self.session = None
        self.version = "v2.1"
        self.uptime = datetime.utcnow()
        richConsole.print(
            '[bold green][Fresh][/] Connecting to Discord...', end='\r')

    async def on_ready(self):
        if not self._init:
            self._init = True
            self.session = aiohttp.ClientSession()
            richConsole.print('[bold green][Fresh][/] Connected.')
        await self.change_presence(
            status=discord.Status.dnd,
            activity=discord.Activity(
                type=discord.ActivityType.watching, name=f"/help | {len(self.guilds)} guilds..")
        )
        self.invite_url = discord.utils.oauth_url(self.user.id)
        if _config['database']['enabled'] is not False:
            collection = _config["database"]["collection"]
            self.db = pymongo.MongoClient(
                _config["database"]["uri"])[collection]
            richConsole.print(
                f'[bold green][Fresh][/] DB: Connected to {collection}!')
        await self.init_extensions()

    async def init_extensions(self):
        extLoaded = 1
        extensions = [e for e in os.listdir('extensions') if e.endswith('.py')]
        with richConsole.status("[bold green][Fresh][/] Loading Extensions...") as status:
            for ext in extensions:
                try:
                    await self.load_extension(f'extensions.{ext[:-3]}')
                    status.update(
                        f"[bold green][Fresh][/] Loading Extensions... [{extLoaded}/{len(extensions)+1}]")
                    extLoaded += 1
                    await asyncio.sleep(0.2)
                except commands.ExtensionAlreadyLoaded:
                    pass
                except Exception as e:
                    richConsole.print(f'[bold red][Fresh][/] ERR: {str(e)}')
            try:
                await self.load_extension('jishaku')
                status.update(
                    f"[bold green][Fresh][/] Loading Extensions... [{extLoaded}/{len(extensions)+1}]")
                extLoaded += 1
            except Exception as e:
                richConsole.print(
                    f'[bold red][Fresh][/] ERR loading Jishaku: {str(e)}')

            richConsole.print(
                f'[bold green][Fresh][/] Succesfully loaded {len(extensions)+1} extensions!')
        with richConsole.status("[bold green][Fresh][/] Attempting to sync application commands...") as status:
            try:
                synced = await self.tree.sync()
                await asyncio.sleep(2)
            except Exception as e:
                richConsole.print(
                    f'[bold red][Fresh][/] Failed to sync application commands:\n{e}')
            richConsole.print(
                f'[bold green][Fresh][/] Synced {len(synced)} commands!')


fresh = Fresh(command_prefix=commands.when_mentioned_or(
    _config.get('prefix')), max_message=None, intents=discord.Intents.all())
fresh.run(_config.get('token'))
