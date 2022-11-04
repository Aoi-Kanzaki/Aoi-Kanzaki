import os
import json
import discord
import aiohttp
import asyncio
import random
from datetime import datetime
from discord.ext import commands
import motor.motor_asyncio as motor

from rich.console import Console as RichConsole

with open("config.json", "r") as config:
    _config = json.load(config)


class Aoi(commands.AutoShardedBot):
    def __init__(self, **options):
        super().__init__(**options)
        self.started = datetime.utcnow()
        self._init = False
        self.config = _config
        self.session = None
        self.version = "v3"
        self.uptime = datetime.utcnow()
        self.richConsole = RichConsole()
        self.richConsole.print(
            '[bold green][Aoi][/] Connecting to Discord...', end='\r')

    async def on_ready(self):
        if not self._init:
            self._init = True
            self.session = aiohttp.ClientSession()
            self.richConsole.print('[bold green][Aoi][/] Connected.')
        self.invite_url = discord.utils.oauth_url(self.user.id)
        if _config['database']['enabled'] is not False:
            collection = _config["database"]["collection"]
            self.db = motor.AsyncIOMotorClient(
                _config["database"]["uri"])[collection]
            self.richConsole.print(
                f'[bold green][Aoi][/] DB: Connected to {collection}!')
        await self.init_extensions()

    async def status_loop(self):
        await self.wait_until_ready()

        while not self.is_closed():
            playing = 0
            for player in self.lavalink.player_manager.players:
                player = self.lavalink.player_manager.get(player)
                if player.current is not None:
                    playing += 1

            statuses = [
                {"name": "guilds",
                    "value": f"/help | {len(self.guilds)} guilds.."},
                {"name": "music",
                    "value": f"music in {playing} guilds.."}
            ]
            status = random.choice(statuses)
            if status['name'] == "guilds":
                await self.change_presence(status=discord.Status.dnd, activity=discord.Activity(
                    type=discord.ActivityType.watching, name=status['value']
                ))
            elif status['name'] == "music":
                await self.change_presence(status=discord.Status.dnd, activity=discord.Activity(
                    type=discord.ActivityType.listening, name=status['value']
                ))

            await asyncio.sleep(30)

    async def init_extensions(self):
        extLoaded = 1
        extensions = [e for e in os.listdir('extensions') if e.endswith('.py')]
        with self.richConsole.status("[bold green][Aoi][/] Loading Extensions...") as status:
            for ext in extensions:
                try:
                    await self.load_extension(f'extensions.{ext[:-3]}')
                    status.update(
                        f"[bold green][Aoi][/] Loading Extensions... [{extLoaded}/{len(extensions)+1}]")
                    extLoaded += 1
                    await asyncio.sleep(0.2)
                except commands.ExtensionAlreadyLoaded:
                    pass
                except Exception as e:
                    self.richConsole.print(
                        f'[bold red][Aoi][/] ERR: {str(e)}')
            try:
                await self.load_extension('jishaku')
                status.update(
                    f"[bold green][Aoi][/] Loading Extensions... [{extLoaded}/{len(extensions)+1}]")
                extLoaded += 1
            except Exception as e:
                self.richConsole.print(
                    f'[bold red][Aoi][/] ERR loading Jishaku: {str(e)}')

            self.richConsole.print(
                f'[bold green][Aoi][/] Succesfully loaded {len(extensions)+1} extensions!')
        try:
            self.loop.create_task(self.status_loop())
            self.richConsole.print('[bold green][Aoi][/] Started Status loop.')
        except Exception as e:
            self.richConsole.print(
                f'[bold red][Aoi][/] Failed to start Status loop: {e}')
        with self.richConsole.status("[bold green][Aoi][/] Attempting to sync application commands...") as status:
            try:
                synced = await self.tree.sync()
                await asyncio.sleep(2)
            except Exception as e:
                self.richConsole.print(
                    f'[bold red][Aoi][/] Failed to sync application commands:\n{e}')
            self.richConsole.print(
                f'[bold green][Aoi][/] Synced {len(synced)} commands!')


Aoi = Aoi(command_prefix=commands.when_mentioned_or(
    _config.get('prefix')), max_message=None, intents=discord.Intents.all())
Aoi.run(_config.get('token'))
