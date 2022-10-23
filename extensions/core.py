import os
import sys
import time
import codecs
import pathlib
import discord
import asyncio
import traceback
import lavalink
from datetime import datetime
from discord.ext import commands
from discord import app_commands as Fresh


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return f'{num:3.1f}{unit}{suffix}'
        num /= 1024.0
    return f'{num:.1f}Yi{suffix}'


class Core(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    def is_dev():
        def predicate(interaction: discord.Interaction) -> bool:
            return interaction.user.id in interaction.client.config['slashCommands']['devIDS']
        return Fresh.check(predicate)

    @Fresh.command(name="invite")
    @Fresh.checks.cooldown(1, 5)
    async def invite(self, interaction: discord.Interaction):
        """Invite the bot to your server!"""
        return await interaction.response.send_message(
            content=f"You can invite the bot here: {self.bot.invite_url}\nSupport URL: <https://discord.gg/WxTmcYG4Ay>",
            ephemeral=True
        )

    @Fresh.command(name="sync")
    @is_dev()
    async def sync(self, interaction: discord.Interaction):
        """Sync's the bot's application commands."""
        await interaction.response.defer(ephemeral=True)
        try:
            synced = await self.bot.tree.sync()
            return await interaction.followup.send(
                content=f"📡 I have succesfully synced {len(synced)} commands!"
            )
        except Exception as e:
            print(e)
            em = discord.Embed(colour=discord.Colour.red(),
                               title="An Error has Occurred:")
            em.description = e
            em.timestamp(time.localtime())
            await interaction.followup.send(embed=e)

    @Fresh.command(name="reload")
    @is_dev()
    async def reload(self, interaction: discord.Interaction, module: str):
        """Reload the bot's modules."""
        loadedModules = [e.__name__ for e in self.bot.extensions.values()]
        response = ""
        extension = f'extensions.{module}'
        response += f"{module}\n"
        if extension in loadedModules:
            steps = [('module_unload', self.bot.unload_extension),
                     ('module_load', self.bot.load_extension)]
        elif extension not in loadedModules:
            steps = [('module_load', self.bot.load_extension)]
        for name, step in steps:
            try:
                await step(extension)
            except commands.errors.ExtensionNotFound:
                response += "  Extension not found\n"
            except commands.errors.ExtensionError as error:
                original = error.original
                response += f'  {name}: {original.__class__.__name__ + ": " + str(original)}\n'
            except Exception as exception:
                response += f'  {name}: {str(exception)}\n'
                traceback.print_exc()
            else:
                response += f'  {name}: {"Good"}\n'
        e = discord.Embed(colour=discord.Colour.teal())
        e.description = response.strip()
        return await interaction.response.send_message(embed=e, ephemeral=True)

    @Fresh.command(name="ping")
    async def ping(self, interaction: discord.Interaction):
        """Check the bots response time."""
        await interaction.response.send_message(f"Latency: `{round(self.bot.latency * 1000)}ms`")

    @Fresh.command(name="about")
    async def about(self, interaction: discord.Interaction):
        """Shows information about Fresh."""
        if not (guild := interaction.guild):
            return await interaction.response.send_message(
                content="This command needs to be ran in a guild!",
                ephemeral=True
            )
        if not (me := guild.me):
            return await interaction.response.send_message(
                content="This command needs to be ran in a guild!",
                ephemeral=True
            )

        total = 0
        file_amount = 0
        for path, subdirs, files in os.walk("."):
            for name in files:
                if name.endswith(".py"):
                    file_amount += 1
                    with codecs.open("./" + str(pathlib.PurePath(path, name)), "r", "utf-8") as f:
                        for i, l in enumerate(f):
                            if (l.strip().startswith("#") or len(l.strip()) == 0):
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

        await interaction.response.send_message(
            embed=discord.Embed(
                title="About Fresh:",
                colour=discord.Colour.teal(),
                description=(
                    f"Authored by <@827940585201205258>. See all contributors on "
                    f"[GitHub](https://github.com/JonnyBoy2000/Fresh). "),
                url="https://github.com/JonnyBoy2000/Fresh",
                timestamp=datetime.now()
            )
            .set_thumbnail(url=me.avatar.url)
            .set_footer(
                text=f"Requested by {interaction.user.display_name}", icon_url=interaction.user.avatar)
            .add_field(name="Bot Version", value=self.bot.version)
            .add_field(name="Python Version",
                       value=f"v{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
            .add_field(name="Discord Version", value=f"v{discord.__version__}")
            .add_field(name="Latest Changes:", value=revision, inline=False)
            .add_field(name="Code Information:", value=code)
        )

    @Fresh.command(name="commits")
    async def commits(self, interaction: discord.Interaction):
        """Shows last 5 github commits."""
        cmd = r'git show -s HEAD~5..HEAD --format="[{}](https://github.com/JonnyBoy2000/Fresh/commit/%H) %s (%cr)"'
        if os.name == "posix":
            cmd = cmd.format(r"\`%h\`")
        else:
            cmd = cmd.format(r"`%h`")
        try:
            revision = os.popen(cmd).read().strip()
        except OSError:
            revision = "Could not fetch due to memory error. Sorry."
        await interaction.response.send_message(
            embed=discord.Embed(
                colour=discord.Colour.teal(),
                description=revision
            )
            .set_author(icon_url=self.bot.user.avatar,
                        name="Latest Github Changes:")
            .set_thumbnail(
                url="https://avatars2.githubusercontent.com/u/22266893?s=400&u=9df85f1c8eb95b889fdd643f04a3144323c38b66&v=4")
        )

    @Fresh.command(name="uptime")
    async def uptime(self, interaction: discord.Interaction):
        """Shows the uptime of the bot."""
        uptime = uptime = self.get_bot_uptime()
        await interaction.response.send_message(
            content=uptime,
            ephemeral=True
        )

    def get_bot_uptime(self, *, brief=False):
        now = datetime.utcnow()
        delta = now - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        if not brief:
            fmt = "I've been online for {d} days, {h} hours, {m} minutes, and {s} seconds!"
        else:
            fmt = "{d}d {h}h {m}m {s}s"
        return fmt.format(d=days, h=hours, m=minutes, s=seconds)

    @Fresh.command(name="musicstats")
    @is_dev()
    async def musicstats(self, interaction: discord.Interaction):
        """Shows the current stats for music."""
        for node in self.bot.lavalink.node_manager.nodes:
            stats = node.stats
            ud, uh, um, us = lavalink.utils.parse_time(stats.uptime)
        return await interaction.response.send_message(
            embed=discord.Embed(
                colour=discord.Colour.teal(),
                title='Lavalink Node Stats')
            .add_field(
                name=node.name,
                value=f'Uptime: {ud:.0f}d {uh:.0f}h{um:.0f}m{us:.0f}s\n'
                f'Players: {stats.players} ({stats.playing_players} playing)\n'
                f'Memory: {sizeof_fmt(stats.memory_used)}/{sizeof_fmt(stats.memory_reservable)}\n'
                'CPU:\n'
                f'\u200b\tCores: {stats.cpu_cores}\n'
                f'\u200b\tSystem Load: {stats.system_load * 100:.2f}%\n'
                f'\u200b\tLavalink Load: {stats.lavalink_load * 100:.2f}%\n'
                'Frames:\n'
                f'\u200b\tSent: {stats.frames_sent}\n'
                f'\u200b\tNulled: {stats.frames_nulled}\n'
                f'\u200b\tDeficit: {stats.frames_deficit}\n'
                f'Node Penalty: {stats.penalty.total:.2f}',
                inline=True
            ),
            ephemeral=True
        )


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(Core(bot))
