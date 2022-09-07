import os
import sys
import glob
import time
import codecs
import pathlib
import discord
import asyncio
from discord.ext import commands
from discord import app_commands as Fresh

class Dev(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @Fresh.command(name="musicstats")
    async def musicstats(self, interaction: discord.Interaction):
        """Shows music stats."""
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

    @Fresh.command(name="botinfo")
    async def botinfo(self, interaction: discord.Interaction):
        """Shows info about the bot."""
        await interaction.response.defer(thinking=False)
        await asyncio.sleep(3)
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
        await interaction.followup.send(embed=e)

    @Fresh.command()
    async def ping(self, interaction: discord.Interaction):
        """Pong!"""
        pings = []
        number = 0
        typings = time.monotonic()
        await interaction.channel.typing()
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

    # @Fresh.command(name="reload")
    # @commands.check(_checks.is_owner)
    # async def reload(interaction: discord.Interaction, folder: str, file: str):
    #     """Reload's one of the bot's extentions."""
    #     await interaction.response.defer(ephemeral=True)
    #     paginator = commands.Paginator(prefix='', suffix='')
    #     if file == "jishaku":
    #         extension = "jishaku"
    #     else:
    #         extension = f"{folder}.{file}"
    #     method, icon = (
    #         (self.bot.reload_extension, "\N{CLOCKWISE RIGHTWARDS AND LEFTWARDS OPEN CIRCLE ARROWS}")
    #         if extension in self.bot.extensions else
    #         (self.bot.load_extension, "\N{INBOX TRAY}")
    #     )
    #     try:
    #         await discord.utils.maybe_coroutine(method, extension)
    #         paginator.add_line(f"{icon} `{extension}`", empty=True)
    #     except Exception as exc:  # pylint: disable=broad-except
    #         traceback_data = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__, 1))
    #         paginator.add_line(
    #             f"{icon}\N{WARNING SIGN} `{extension}`\n```py\n{traceback_data}\n```",
    #             empty=True
    #         )
    #     for page in paginator.pages:
    #         await interaction.followup.send(page)

    # @Fresh.command(name="unload")
    # @commands.check(_checks.is_owner)
    # async def unload(interaction: discord.Interaction, folder: str, file: str):
    #     await interaction.response.defer(ephemeral=True)
    #     paginator = commands.Paginator(prefix='', suffix='')
    #     icon = "\N{OUTBOX TRAY}"
    #     if file == "jishaku":
    #         extension = "jishaku"
    #     else:
    #         extension = f"{folder}.{file}"
    #     if extension not in self.bot.extensions:
    #         return await interaction.followup.send("This module wasn't even loaded. Not proceeding...")
    #     else:
    #         try:
    #             await discord.utils.maybe_coroutine(self.bot.unload_extension, extension)
    #             paginator.add_line(f"{icon} `{extension}`", empty=True)
    #         except Exception as exc:
    #             traceback_data = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__, 1))

    #             paginator.add_line(
    #                 f"{icon}\N{WARNING SIGN} `{extension}`\n```py\n{traceback_data}\n```",
    #                 empty=True
    #             )
    #         for page in paginator.pages:
    #             await interaction.followup.send(page)

    # @reload.autocomplete('file')
    # @unload.autocomplete('file')
    # async def extension_auto(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    #     files = []
    #     for key in self.bot.config['enabledModules']:
    #         if key == "jishaku":
    #             name = "jishaku"
    #         else:
    #             name = key.split('.')[1]
    #         files.append(name)
    #     return [
    #         app_commands.Choice(name=file, value=file)
    #         for file in files if current.lower() in file.lower()
    #     ]

    # @reload.autocomplete('folder')
    # @unload.autocomplete('folder')
    # async def folder_auto(interaction: discord.Interaction, current: str) -> List[app_commands.Choice[str]]:
    #     folders = ["cogs", "utils"]
    #     return [
    #         app_commands.Choice(name=folder, value=folder)
    #         for folder in folders if current.lower() in folder.lower()
    #    ]

    # @Fresh.command(name="modules")
    # @commands.check(_checks.is_owner)
    # async def modules(interaction: discord.Interaction):
    #     """Shows modules."""
    #     loaded = [c.__module__.split(".")[1] for c in bot.cogs.values()]
    #     unloaded = [c.split(".")[1] for c in self._list_modules() if c.split(".")[1] not in loaded]
    #     if not unloaded:
    #         unloaded = ["All modules are loaded"]
    #     e = discord.Embed(colour=discord.Colour.blurple())
    #     e.set_author(name="Modules.", icon_url=bot.user.avatar)
    #     e.add_field(name="Loaded Modules:", value=", ".join(sorted(loaded)), inline=False)
    #     e.add_field(name="Unloaded Modules:", value=", ".join(sorted(unloaded)), inline=False)
    #     return await interaction.response.send_message(embed=e, ephemeral=True)

async def setup(bot):
    await bot.add_cog(Dev(bot))