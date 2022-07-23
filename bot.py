import discord
import os
import json
import aiohttp
import datetime
import aiosqlite
import random
import asyncio
from colr import color
from pymongo import MongoClient
from discord.ext import commands
from discord import app_commands

load_cogs = [
	'cogs.music',
	'cogs.dev',
	'cogs.levels',
	'cogs.utility',
	'cogs.economy',
	'cogs.fun'
]
load_utils = [
	'utils.errorhandler',
	'utils.leveling',
	'utils.help',
	'utils.support_join'
]

starttime = datetime.datetime.now()

with open('config.json', 'r') as config:
	_config = json.load(config)

async def _prefix(bot, msg):
	with open('./data/prefixes.json', 'r') as f:
		prefixes = json.load(f)
	if msg.guild is None:
		return _config['prefix']
	else:
		return prefixes[str(msg.guild.id)]

MY_GUILD = discord.Object(id=_config['guildid'])
class Fresh(commands.AutoShardedBot):
	def __init__(self):
		super().__init__(command_prefix=_prefix, description="", pm_help=None, case_insensitive=True, intents=discord.Intents.all())
		self.version = "v1.0.0"
		self.spotify_id = _config['spotify_id']
		self.spotify_secret = _config['spotify_secret']
		self.stats = {}
		self.sniped = []
		self.uptime = datetime.datetime.utcnow()
		self.colors = {
			"blue": (4, 95, 185),
			"cyan": (4, 211, 232),
			"purple": (123, 4, 232),
			"green": (4, 232, 95),
			"red": (189, 16, 16)
		}
		
	async def setup_hook(self):
		# This copies the global commands over to your guild.
		self.tree.copy_global_to(guild=MY_GUILD)
		await self.tree.sync(guild=MY_GUILD)

	async def on_guild_join(self, guild):
		with open('./data/prefixes.json', 'r') as f:
			prefixes = json.load(f)
		prefixes[str(guild.id)] = "f?"
		with open('./data/prefixes.json', 'w') as f:
			json.dump(prefixes, f, indent=4)

	async def on_guild_remove(self, guild):
		with open('./data/prefixes.json', 'r') as f:
			prefixes = json.load(f)
		prefixes.pop(str(guild.id))
		with open('./data/prefixes.json', 'w') as f:
			json.dump(prefixes, f, indent=4)
			
	async def clear_screen(self):
		if os.name == "nt":
			os.system("cls")
		else:
			os.system("clear")

	async def on_ready(self):
		await self.clear_screen()
		await asyncio.sleep(1)
		self.session = aiohttp.ClientSession()
		channels = len([c for c in self.get_all_channels()])
		login_time = datetime.datetime.now() - starttime
		login_time = login_time.seconds + login_time.microseconds/1E6
		print(color("-----------------------------------------------------------------", fore=self.colors["blue"]))
		print(color("Login time         :", fore=self.colors["cyan"]), color(f"{login_time} milliseconds", fore=self.colors["purple"]))
		print(color("Logged in as       :", fore=self.colors["cyan"]), color(f"{str(self.user.name)} ({self.user.id})", fore=self.colors["purple"]))
		print(color("Connected to       :", fore=self.colors["cyan"]), color(f"{len(self.guilds)} guilds and {channels} channels", fore=self.colors["purple"]))
		print(color("Python version     :", fore=self.colors["cyan"]), color("{}.{}.{}".format(*os.sys.version_info[:3]), fore=self.colors["purple"]))
		print(color("Discord.py version :", fore=self.colors["cyan"]), color(f"{discord.__version__}", fore=self.colors["purple"]))
		if _config['mongoURI'] != "":
			self.database = MongoClient(_config['mongoURI'])
			print(color("Database Status    :", fore=self.colors['cyan']), color("Should be connected!", fore=self.colors['purple']))
		else:
			print(color("Database Status    :", fore=self.colors['cyan']), color("Not Enabled.", fore=self.colors['purple']))
		print(color("-----------------------------------------------------------------", fore=self.colors["blue"]))
		try:
			await self.load_extension("jishaku")
			print(color("Loaded JSK on first try!", fore=self.colors["green"]))
		except Exception as e:
			print(color(f"Failed to load JSK! Reason:\n{e}", fore=self.colors["red"]))
		for module in load_cogs:
			try:
				await self.load_extension(module)
			except Exception as e:
				print(color(f'{e}', fore=self.colors["red"]))
		for module in load_utils:
			try:
				await self.load_extension(module)
			except Exception as e:
				print(color(f'{e}', fore=self.colors["red"]))

	async def on_command(self, ctx):
		module = ctx.command.cog_name
		cmd_name = ctx.command.name
		if module not in self.stats:
			self.stats[module] = {cmd_name: 1}
		elif cmd_name not in self.stats[module]:
			self.stats[module][cmd_name] = 1
		else:
			self.stats[module][cmd_name] += 1

	async def is_on_cd(self, ctx):
		"""Assign a default CD if the command was defined without one. Raise CommandOnCooldown error if it is on CD."""
		if await self.is_owner(ctx.author) is True:
			return True
		await self.handle_command_cooldown(ctx)
		return True

	async def raise_if_on_cd(self, buckets):
		"""Raise a CommandOnCooldown error, only if a command is on cooldown."""
		retry_after = buckets._cooldown.update_rate_limit()
		if retry_after:
			raise commands.errors.CommandOnCooldown(buckets._cooldown, retry_after)

	async def handle_command_cooldown(self, ctx):
		"""Assign a default CD if needed. Raise error if the specific command is on CD."""
		buckets = getattr(ctx.command, '_buckets')
		await self.assign_default_cooldown(buckets)
		if ctx.command.is_on_cooldown(ctx):
			await self.raise_if_on_cd(buckets)

	async def assign_default_cooldown(self, buckets):
		"""Assigns a default cooldown to a command which was defined without one."""
		if buckets._cooldown is None:
			buckets._cooldown = commands.Cooldown(5, 30.0, commands.BucketType.user)
        
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
