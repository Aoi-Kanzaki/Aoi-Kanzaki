import os
import sys
import glob
import time
import codecs
import pathlib
import discord
from utils import _checks
from discord.ext import commands
from asyncio.subprocess import PIPE


class Dev(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        fresh = bot.tree

        @fresh.command(name="modules")
        @commands.check(_checks.is_owner)
        async def modules(interaction: discord.Interaction):
            """Shows modules."""
            loaded = [c.__module__.split(".")[1] for c in bot.cogs.values()]
            unloaded = [c.split(".")[1] for c in self._list_modules() if c.split(".")[1] not in loaded]
            if not unloaded:
                unloaded = ["All modules are loaded"]
            e = discord.Embed(colour=discord.Colour.blurple())
            e.set_author(name="Modules.", icon_url=bot.user.avatar)
            e.add_field(name="Loaded Modules:", value=", ".join(sorted(loaded)), inline=False)
            e.add_field(name="Unloaded Modules:", value=", ".join(sorted(unloaded)), inline=False)
            return await interaction.response.send_message(embed=e, ephemeral=True)

        @fresh.command(name="lavalinkstats")
        async def lavalink(interaction: discord.Interaction):
            """Shows lavalink music stats."""
            try:
                lavalink = self.bot.lavalink
            except AttributeError:
                return interaction.response.send_message(
                    "Music is not enabled to I'm not playing in any servers!", ephemeral=True)
            server_num = len([p for p in lavalink.player_manager.players.values() if p.is_playing])
            server_ids = lavalink.player_manager.players
            server_list = []
            number = 0
            users = 0
            for _id, p in server_ids.items():
                try:
                    if p.is_playing:
                        number += 1
                        g = self.bot.get_guild(_id)
                        users += len(g.me.voice.channel.members)
                        server_list.append(f"`{number}.` {g.name}: **{p.current.title}**")
                    else:
                        server_list.append(f"`{number}.` {g.name}: **Nothing playing.**")
                except AttributeError:
                    pass
            if server_list == []:
                servers = "Not connected anywhere."
            else:
                servers = "\n".join(server_list)
            e = discord.Embed()
            e.colour = discord.Colour.blurple()
            e.add_field(name="Players:", value=f"Playing in {len(server_list)} servers..")
            e.add_field(name="Users:", value=f"{users-len(server_list)} users listening..")
            e.add_field(name="Guilds:", value=servers, inline=False)
            e.set_footer(text=f"There is currently {len(server_ids)} players created in total.")
            e.set_thumbnail(url=self.bot.user.avatar)
            try:
                return await interaction.response.send_message(embed=e)
            except discord.HTTPException:
                return await interaction.response.send_message(
                        f"I can't display all the servers. But I am currently playing in {server_num} servers.**")

        @fresh.command(name="botinfo")
        async def botinfo(interaction: discord.Interaction):
            """Shows info about the bot."""
            total = 0
            file_amount = 0
            pyvi = sys.version_info
            discordi = f"Discord.py: v{discord.__version__} (Branch rewrite)"
            python = f"Python: v{pyvi.major}.{pyvi.minor}.{pyvi.micro} (Branch {pyvi.releaselevel} v{pyvi.serial})"
            dev = await self.bot.http.get_user(827940585201205258)
            devn = f"{dev['username']}#{dev['discriminator']}"
            for path, subdirs, files in os.walk("."):
                for name in files:
                    if name.endswith(".py"):
                        file_amount += 1
                        with codecs.open("./" + str(pathlib.PurePath(path, name)), "r", "utf-8") as f:
                            for i, l in enumerate(f):
                                if (l.strip().startswith("#") or len(l.strip()) == 0):  # skip commented lines.
                                    pass
                                else:
                                    total += 1
            code = f"I am made of {total:,} lines of Python, spread across {file_amount:,} files!"
            cmd = r'git show -s HEAD~3..HEAD --format="[{}](https://github.com/JonnyBoy2000/Fresh/commit/%H) %s (%cr)"'
            if os.name == "posix":
                cmd = cmd.format(r"\`%h\`")
            else:
                cmd = cmd.format(r"`%h`")
            try:
                revision = os.popen(cmd).read().strip()
            except OSError:
                revision = "Could not fetch due to memory error. Sorry."
            e = discord.Embed()
            e.colour = discord.Colour.blurple()
            e.add_field(name="Developer:", value=devn)
            e.add_field(name="Libraries:", value=f"{discordi}\n{python}")
            e.add_field(name="Latest Changes:", value=revision, inline=False)
            e.add_field(name="Code Information:", value=code)
            e.set_author(name=f"F.res.h {self.bot.version}", icon_url=interaction.user.avatar)
            e.set_thumbnail(url=self.bot.user.avatar)
            await interaction.response.send_message(embed=e)

        @fresh.command()
        async def ping(interaction: discord.Interaction):
            """Pong!"""
            pings = []
            number = 0
            typings = time.monotonic()
            await interaction.channel.typing()
            typinge = time.monotonic()
            typingms = round((typinge - typings) * 1000)
            pings.append(typingms)
            latencyms = round(bot.latency * 1000)
            pings.append(latencyms)
            discords = time.monotonic()
            url = "https://discordapp.com/"
            async with bot.session.get(url) as resp:
                if resp.status == 200:
                    discorde = time.monotonic()
                    discordms = round((discorde - discords) * 1000)
                    pings.append(discordms)
                    discordms = f"{discordms}ms"
                else:
                    discordms = "Failed"
            for ms in pings:
                number += ms
            average = round(number / len(pings))
            await interaction.response.send_message(
                f"__**Ping Times:**__\nTyping: `{typingms}ms`  |  Latency: `{latencyms}ms`\nDiscord: `{discordms}`  |  Average: `{average}ms`")

    def _list_modules(self):
        modules = [os.path.basename(f) for f in glob.glob("cogs/*.py")]
        return ["cogs." + os.path.splitext(f)[0] for f in modules]


async def setup(bot):
    await bot.add_cog(Dev(bot))