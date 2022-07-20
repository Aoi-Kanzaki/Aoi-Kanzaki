import discord
import os
import glob
import datetime
import typing
from utils import checks
from discord.ext import commands

class Dev(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.check(checks.is_owner)
    async def modules(self, ctx):
        """Shows modules."""
        loaded = [c.__module__.split(".")[1] for c in self.bot.cogs.values()]
        unloaded = [c.split(".")[1] for c in self._list_modules() if c.split(".")[1] not in loaded]
        if not unloaded:
            unloaded = ['All modules are loaded']
        e = discord.Embed()
        e.colour = 0x36393E
        e.set_author(name="Modules.", icon_url=self.bot.user.avatar)
        e.add_field(name="Loaded Modules:", value=", ".join(sorted(loaded)), inline=False)
        e.add_field(name="Unloaded Modules:", value=", ".join(sorted(unloaded)), inline=False)
        await ctx.send(embed=e)

    @commands.command()
    @commands.guild_only()
    async def clean(self, ctx):
        """Clean bot messages and command messages."""
        can_mass_purge = ctx.channel.permissions_for(ctx.guild.me).manage_messages
        await ctx.channel.purge(limit=100, check=lambda m: m.author == ctx.bot.user, before=ctx.message, after=datetime.datetime.now() - datetime.timedelta(days=14), bulk=can_mass_purge)
        try:
            await ctx.channel.purge(limit=100, check=lambda m: (m.content.startswith("f?") or m.content.startswith("F?")), before=ctx.message, after=datetime.datetime.now() - datetime.timedelta(days=14), bulk=can_mass_purge)
        except:
            pass
        await ctx.message.add_reaction('\u2705')

    def _list_modules(self):
        modules = [os.path.basename(f) for f in glob.glob("cogs/*.py")]
        return ["cogs." + os.path.splitext(f)[0] for f in modules]

async def setup(bot):
   await bot.add_cog(Dev(bot))