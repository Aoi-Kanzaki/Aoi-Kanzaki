import os
import json
import discord
import pymongo
import aiohttp
from datetime import datetime
from discord.ext import commands

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
        print('[Fresh] Connecting to Discord...', end='\r')

    async def on_ready(self):
        if not self._init:
            self._init = True
            self.session = aiohttp.ClientSession()
            print('\x1b[2K[Fresh] Connected.')
        await self.change_presence(
            status=discord.Status.dnd,
            activity=discord.Activity(
                type=discord.ActivityType.watching, name=f"/help | {len(self.guilds)} guilds..")
        )
        self.invite_url = discord.utils.oauth_url(self.user.id)
        if _config["database"]["enabled"] != False:
            collection = _config["database"]["collection"]
            self.db = pymongo.MongoClient(
                _config["database"]["uri"])[collection]
            print(f'\x1b[2K[Fresh] DB: Connected to {collection}!')
        await self.load_extension('extensions.core')
        await self.init_extensions()

    async def init_extensions(self):
        try:
            await self.load_extension('jishaku')
            print('\x1b[2K[Fresh] Loaded Jishaku!')
        except Exception as e:
            print(f'\x1b[2K{ext:20}ERR loading Jishaku: {str(e)}')
        for ext in os.listdir('extensions'):
            if not ext.endswith('.py') or ext.startswith('core') or ext.startswith('_'):
                continue
            try:
                await self.load_extension(f'extensions.{ext[:-3]}')
            except Exception as e:
                print(f'\x1b[2K{ext:20}ERR: {str(e)}')
            except commands.ExtensionAlreadyLoaded:
                pass
            else:
                print(f'\x1b[2K{ext:20}OK', end='\r')
        try:
            print('\x1b[2K[Fresh] Attempting to sync application commands...')
            synced = await self.tree.sync()
            print(f'\x1b[2K[Fresh] Synced {len(synced)} commands!')
        except Exception as e:
            print(f'\x1b[2K[Fresh] Failed to sync application commands:\n{e}')
        print(
            f'\x1b[2K[Fresh] Loaded {len(self.extensions)} extensions into memory.')


fresh = Fresh(command_prefix=commands.when_mentioned_or(
    _config.get('prefix')), max_message=None, intents=discord.Intents.all())
fresh.run(_config.get('token'))
