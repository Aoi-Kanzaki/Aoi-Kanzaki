import discord
import os
import json
import aiohttp
import datetime
import asyncio
import aiosqlite
from colr import color
from discord.ext import commands
from utils._checks import check_commands
from motor.motor_asyncio import AsyncIOMotorClient

starttime = datetime.datetime.now()
with open('config.json', 'r') as config:
	_config = json.load(config)
class Fresh(commands.AutoShardedBot):
	def __init__(self):
		super().__init__(command_prefix=commands.when_mentioned_or(self.get_prefix), description="", pm_help=None, case_insensitive=True, intents=discord.Intents.all())
		self.version = "v1.0.0"
		self.spotify_id = _config['spotify_id']
		self.spotify_secret = _config['spotify_secret']
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
			"yellow": (163, 187, 3)
		}
	
	async def get_prefix(bot, message):
		async with aiosqlite.connect("./data/prefixes.db") as db:
			getData = await db.execute("SELECT * FROM prefixs WHERE guild = ?", (message.guild.id,))
			data = await getData.fetchone()
			if data is None:
				return _config['prefix']
			else:
				return data[0]
			
	async def clear_screen(self):
		if os.name == "nt":
			os.system("cls")
		else:
			os.system("clear")
			
	async def load_modules(self):
		try:
			await self.load_extension("jishaku")
			print(color("Loaded JSK on first try!", fore=self.colors["green"]))
		except Exception as e:
			print(color(f"Failed to load JSK! Reason:\n{e}", fore=self.colors["red"]))
		dirs = ['./functions', './cogs', './utils']
		for d in dirs:
			for module in os.listdir(d):
				if module.endswith('.py'):
					name = module[:-3]
					if name in ('_checks', '_LavalinkVoiceClient', '_MusicButtons'):
						pass
					else:
						try:
							d = d.replace('./', '')
							await self.load_extension(f'{d}.{name}')
						except Exception as e:
							print(color(f'Failed to load {name}:\n{e}', fore=self.colors["red"]))

	async def connect_to_db(self):
		if _config['mongoURI'] != "":
			self.db = AsyncIOMotorClient(_config['mongoURI'])['db']
			print(color("Database Status    :", fore=self.colors['cyan']), color("Should be connected!", fore=self.colors['purple']))
		else:
			print(color("Database Status    :", fore=self.colors['cyan']), color("Not Enabled.", fore=self.colors['purple']))
		print(color("+-----------------------------------------------------------+", fore=self.colors["blue"]))
		if not os.path.exists("./data/"):
			os.makedirs("./data/")
			print(color("Data folder was not found, the new directory was created!", fore=self.colors['green']))

	async def on_ready(self):
		await self.clear_screen()
		await asyncio.sleep(1)
		self.session = aiohttp.ClientSession()
		channels = len([c for c in self.get_all_channels()])
		login_time = datetime.datetime.now() - starttime
		login_time = login_time.seconds + login_time.microseconds/1E6
		print(color("+-----------------------------------------------------------+", fore=self.colors["blue"]))
		print(color("Login time         :", fore=self.colors["cyan"]), color(f"{login_time} milliseconds", fore=self.colors["purple"]))
		print(color("Logged in as       :", fore=self.colors["cyan"]), color(f"{str(self.user.name)} ({self.user.id})", fore=self.colors["purple"]))
		print(color("Connected to       :", fore=self.colors["cyan"]), color(f"{len(self.guilds)} guilds and {channels} channels", fore=self.colors["purple"]))
		print(color("Python version     :", fore=self.colors["cyan"]), color("{}.{}.{}".format(*os.sys.version_info[:3]), fore=self.colors["purple"]))
		print(color("Discord.py version :", fore=self.colors["cyan"]), color(f"{discord.__version__}", fore=self.colors["purple"]))
		await self.connect_to_db()
		await self.load_modules()
		print(color("Syncing commands...", fore=self.colors["yellow"]))
		try:
			synced = await self.tree.sync()
			print(color(f"Synced {len(synced)} commands globaly!", fore=self.colors["green"]))
		except Exception as e:
			print(color(f"Failed to sync commands! Reason:\n{e}", fore=self.colors["red"]))
        
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
			super().run(_config['token'])
		except Exception as e:
			print(color(f'Failed to login:\n{e}', fore=self.colors["red"]))

Fresh().run()
