import os
import sys
import time
import codecs
import pathlib
import discord
import asyncio
import traceback
import lavalink
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
            content=f"You can invite the bot here: {self.bot.invite_url}\nInvite url: <https://discord.gg/WxTmcYG4Ay>",
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

    @Fresh.command(name="botinfo")
    async def botinfo(self, interaction: discord.Interaction):
        """Shows info about the bot."""
        await interaction.response.defer(thinking=False)
        await asyncio.sleep(3)
        total = 0
        file_amount = 0
        pyvi = sys.version_info
        discordi = f"Discord.py: v{discord.__version__}"
        python = f"Python: v{pyvi.major}.{pyvi.minor}.{pyvi.micro} (Branch {pyvi.releaselevel} v{pyvi.serial})"
        dev = await self.bot.http.get_user(827940585201205258)
        devn = f"{dev['username']}#{dev['discriminator']}"
        for path, subdirs, files in os.walk("."):
            for name in files:
                if name.endswith(".py"):
                    file_amount += 1
                    with codecs.open("./" + str(pathlib.PurePath(path, name)), "r", "utf-8") as f:
                        for i, l in enumerate(f):
                            # skip commented lines.
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
        e = discord.Embed()
        e.colour = discord.Colour.blurple()
        e.add_field(name="Developer:", value=devn)
        e.add_field(name="Libraries:", value=f"{discordi}\n{python}")
        e.add_field(name="Latest Changes:", value=revision, inline=False)
        e.add_field(name="Code Information:", value=code)
        e.set_author(name=f"F.res.h {self.bot.version}",
                     icon_url=interaction.user.avatar)
        e.set_thumbnail(url=self.bot.user.avatar)
        await interaction.followup.send(embed=e)

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
        e = discord.Embed()
        e.colour = discord.Colour.blurple()
        e.description = revision
        e.set_author(icon_url=self.bot.user.avatar,
                     name="Latest Github Changes:")
        e.set_thumbnail(
            url="https://avatars2.githubusercontent.com/u/22266893?s=400&u=9df85f1c8eb95b889fdd643f04a3144323c38b66&v=4")
        await interaction.response.send_message(embed=e)

    @Fresh.command(name="musicstats")
    @is_dev()
    async def musicstats(self, interaction: discord.Interaction):
        """Shows the current stats for music."""
        embed = discord.Embed(colour=0x00fefe, title='Lavalink Node Stats')
        for node in self.bot.lavalink.node_manager.nodes:
            stats = node.stats
            ud, uh, um, us = lavalink.utils.parse_time(stats.uptime)
            embed.add_field(
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
            )
        return await interaction.response.send_message(
            embed=embed,
            ephemeral=True
        )


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(Core(bot))
