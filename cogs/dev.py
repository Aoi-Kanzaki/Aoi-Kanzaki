import discord
import time
import asyncio
import os
import glob
from utils import _checks
from discord.ext import commands
from asyncio.subprocess import PIPE

class Dev(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    def _list_modules(self):
        modules = [os.path.basename(f) for f in glob.glob("cogs/*.py")]
        return ["cogs." + os.path.splitext(f)[0] for f in modules]

    @commands.command()
    @commands.check(_checks.is_owner)
    async def modules(self, ctx):
        """Shows modules."""
        loaded = [c.__module__.split(".")[1] for c in self.bot.cogs.values()]
        unloaded = [c.split(".")[1] for c in self._list_modules() if c.split(".")[1] not in loaded]
        if not unloaded:
            unloaded = ['All modules are loaded']
        e = discord.Embed(colour=discord.Colour.blurple())
        e.set_author(name="Modules.", icon_url=self.bot.user.avatar)
        e.add_field(name="Loaded Modules:", value=", ".join(sorted(loaded)), inline=False)
        e.add_field(name="Unloaded Modules:", value=", ".join(sorted(unloaded)), inline=False)
        await ctx.send(embed=e)

    @commands.command()
    @commands.check(_checks.is_owner)
    async def network(self, ctx, *, args=None):
        """Network information."""
        await ctx.typing()
        if not args:
            proc = await asyncio.create_subprocess_shell("vnstati -s -i enp1s0 -o vnstati.png", stdin=None, stderr=None, stdout=PIPE)
            out = await proc.stdout.read()
            await ctx.send(file=discord.File('vnstati.png'))
        elif args == "daily":
            proc = await asyncio.create_subprocess_shell("vnstati -d -i enp1s0 -o vnstati.png", stdin=None, stderr=None, stdout=PIPE)
            out = await proc.stdout.read()
            await ctx.send(file=discord.File('vnstati.png'))
        elif args == "hourly":
            proc = await asyncio.create_subprocess_shell("vnstati -h -i enp1s0 -o vnstati.png", stdin=None, stderr=None, stdout=PIPE)
            out = await proc.stdout.read()
            await ctx.send(file=discord.File('vnstati.png'))
        elif args == "monthly":
            proc = await asyncio.create_subprocess_shell("vnstati -m -i enp1s0 -o vnstati.png", stdin=None, stderr=None, stdout=PIPE)
            out = await proc.stdout.read()
            await ctx.send(file=discord.File('vnstati.png'))

    @commands.command()
    async def ping(self, ctx):
        """ Pong! """
        pings = []
        number = 0
        typings = time.monotonic()
        await ctx.typing()
        typinge = time.monotonic()
        typingms = round((typinge - typings) * 1000)
        pings.append(typingms)
        latencyms = round(self.bot.latency * 1000)
        pings.append(latencyms)
        discords = time.monotonic()
        url = "https://discordapp.com/"
        async with self.bot.session.get(url) as resp:
            if resp.status == 200:
                discorde = time.monotonic()
                discordms = round((discorde-discords)*1000)
                pings.append(discordms)
                discordms = f"{discordms}ms"
            else:
                discordms = "Failed"
        for ms in pings:
            number += ms
        average = round(number / len(pings))
        await ctx.send(f"__**Ping Times:**__\nTyping: `{typingms}ms`  |  Latency: `{latencyms}ms`\nDiscord: `{discordms}`  |  Average: `{average}ms`")

async def setup(bot):
   await bot.add_cog(Dev(bot))