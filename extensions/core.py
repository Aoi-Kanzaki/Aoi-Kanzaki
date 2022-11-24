import io
import os
import sys
import time
import math
import codecs
import pathlib
import discord
import inspect
import traceback
import lavalink
import asyncio
import typing
import psutil
from jishaku.flags import Flags
from datetime import datetime
from discord.ext import commands
from discord import app_commands as Aoi
from utils.checks import is_dev
from jishaku.paginators import PaginatorInterface, WrappedPaginator

from modals.BugReport import BugReport
from modals.Suggest import Suggest


def sizeof_fmt(num, suffix='B'):
    for unit in ['', 'Ki', 'Mi', 'Gi', 'Ti', 'Pi', 'Ei', 'Zi']:
        if abs(num) < 1024.0:
            return f'{num:3.1f}{unit}{suffix}'
        num /= 1024.0
    return f'{num:.1f}Yi{suffix}'


class Core(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    @Aoi.command(name="report")
    @Aoi.checks.cooldown(1, 60)
    async def report(self, interaction: discord.Interaction):
        """Submit a bug report to the developer."""
        return await interaction.response.send_modal(BugReport(self.bot))

    @Aoi.command(name="suggest")
    @Aoi.checks.cooldown(1, 60)
    async def suggest(self, interaction: discord.Interaction):
        """Suggest a feature for the developer."""
        return await interaction.response.send_modal(Suggest(self.bot))

    @Aoi.command(name="invite")
    @Aoi.checks.cooldown(1, 5)
    async def invite(self, interaction: discord.Interaction):
        """Invite the bot to your server!"""
        return await interaction.response.send_message(
            content=f"You can invite the bot here: {self.bot.invite_url}\nSupport URL: <https://discord.gg/WxTmcYG4Ay>",
            ephemeral=True
        )

    @Aoi.command(name="sync")
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
            self.bot.logger.error(f"Failed to sync commands: {e}")
            self.bot.richConsole.print(
                f"[bold red][Aoi][/] Error syncing commands: {e}")
            em = discord.Embed(colour=discord.Colour.red(),
                               title="An Error has Occurred:")
            em.description = e
            em.timestamp(time.localtime())
            await interaction.followup.send(embed=e)

    @Aoi.command(name="reload")
    @Aoi.describe(module="The module to reload.")
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

    @Aoi.command(name="ping")
    async def ping(self, interaction: discord.Interaction):
        """Check the bots response time."""
        await interaction.response.defer()
        message = None
        api_readings: typing.List[float] = []
        websocket_readings: typing.List[float] = []
        for _ in range(5):
            text = "Calculating round-trip time...\n\n"
            text += "\n".join(f"Reading {index + 1}: {reading * 1000:.2f}ms" for index,
                              reading in enumerate(api_readings))
            if api_readings:
                average, stddev = await self.mean_stddev(api_readings)
                text += f"\n\nAverage: {average * 1000:.2f} \N{PLUS-MINUS SIGN} {stddev * 1000:.2f}ms"
            else:
                text += "\n\nNo readings yet."
            if websocket_readings:
                average = sum(websocket_readings) / len(websocket_readings)
                text += f"\nWebsocket latency: {average * 1000:.2f}ms"
            else:
                text += f"\nWebsocket latency: {self.bot.latency * 1000:.2f}ms"
            if message:
                before = time.perf_counter()
                await interaction.followup.edit_message(
                    message_id=message.id, content=text)
                after = time.perf_counter()
                api_readings.append(after - before)
            else:
                before = time.perf_counter()
                message = await interaction.followup.send(content=text)
                after = time.perf_counter()
                api_readings.append(after - before)
            if self.bot.latency > 0.0:
                websocket_readings.append(self.bot.latency)

    @Aoi.command(name="about")
    async def about(self, interaction: discord.Interaction):
        """Shows information about Aoi."""
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

        cmd = r'git show -s HEAD~3..HEAD --format="[{}](https://github.com/Jonny0181/Aoi-Kanzaki/commit/%H) %s (%cr)"'
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
                title="About Aoi:",
                colour=discord.Colour.teal(),
                description=(
                    f"Authored by <@827940585201205258>. See all contributors on "
                    f"[GitHub](https://github.com/Jonny0181/Aoi-Kanzaki). "),
                url="https://github.com/Jonny0181/Aoi-Kanzaki",
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

    @Aoi.command(name="commits")
    async def commits(self, interaction: discord.Interaction):
        """Shows last 5 github commits."""
        cmd = r'git show -s HEAD~5..HEAD --format="[{}](https://github.com/Jonny0181/Aoi-Kanzaki/commit/%H) %s (%cr)"'
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

    @Aoi.command(name="uptime")
    async def uptime(self, interaction: discord.Interaction):
        """Shows the uptime of the bot."""
        uptime = self.get_bot_uptime()
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

    @Aoi.command(name="musicstats")
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

    @Aoi.command(name="source")
    @Aoi.describe(command_name="The command you want to see the source of.")
    @is_dev()
    async def source(self, interaction: discord.Interaction, command_name: str):
        """"Displays the source code for a command."""
        command = self.bot.tree.get_command(command_name)
        if not command:
            await interaction.response.send_message(
                content=f"Couldn't find command `{command_name}`.")
        try:
            source_lines, _ = inspect.getsourcelines(command.callback)
        except (TypeError, OSError):
            return await interaction.response.send_message(
                content=f"Was unable to retrieve the source for `{command}` for some reason.")

        filename = "source.py"

        try:
            filename = pathlib.Path(inspect.getfile(command.callback)).name
        except (TypeError, OSError):
            pass

        source_text = ''.join(source_lines)

        if await self.use_file_check(interaction, len(source_text)):
            await interaction.response.send_message(file=discord.File(
                filename=filename,
                fp=io.BytesIO(source_text.encode('utf-8'))
            ))
        else:
            paginator = WrappedPaginator(
                prefix='```py', suffix='```', max_size=1980)
            paginator.add_line(source_text.replace(
                '```', '``\N{zero width space}`'))
            interface = PaginatorInterface(
                self.bot, paginator, owner=interaction.user)
            await interface.send_to(interaction)

    @Aoi.command(name='sysinfo')
    @is_dev()
    async def psutil(self, interaction: discord.Interaction):
        """Show CPU, Memory, Disk, and Network information"""

        # CPU
        cpu_cs = ("CPU Count"
                  "\n\t{0:<9}: {1:>2}".format("Physical", psutil.cpu_count(logical=False)) +
                  "\n\t{0:<9}: {1:>2}".format("Logical", psutil.cpu_count()))
        psutil.cpu_percent(interval=None, percpu=True)
        await asyncio.sleep(1)
        cpu_p = psutil.cpu_percent(interval=None, percpu=True)
        cpu_ps = ("CPU Usage"
                  "\n\t{0:<8}: {1}".format("Per CPU", cpu_p) +
                  "\n\t{0:<8}: {1:.1f}%".format("Overall", sum(cpu_p)/len(cpu_p)))
        cpu_t = psutil.cpu_times()
        width = max([len("{:,}".format(int(n)))
                    for n in [cpu_t.user, cpu_t.system, cpu_t.idle]])
        cpu_ts = ("CPU Times"
                  "\n\t{0:<7}: {1:>{width},}".format("User", int(cpu_t.user), width=width) +
                  "\n\t{0:<7}: {1:>{width},}".format("System", int(cpu_t.system), width=width) +
                  "\n\t{0:<7}: {1:>{width},}".format("Idle", int(cpu_t.idle), width=width))

        # Memory
        mem_v = psutil.virtual_memory()
        width = max([len(self._size(n)) for n in [mem_v.total,
                    mem_v.available, (mem_v.total - mem_v.available)]])
        mem_vs = ("Virtual Memory"
                  "\n\t{0:<10}: {1:>{width}}".format("Total", self._size(mem_v.total), width=width) +
                  "\n\t{0:<10}: {1:>{width}}".format("Available", self._size(mem_v.available), width=width) +
                  "\n\t{0:<10}: {1:>{width}} {2}%".format("Used", self._size(mem_v.total - mem_v.available),
                                                          mem_v.percent, width=width))
        mem_s = psutil.swap_memory()
        width = max([len(self._size(n))
                    for n in [mem_s.total, mem_s.free, (mem_s.total - mem_s.free)]])
        mem_ss = ("Swap Memory"
                  "\n\t{0:<6}: {1:>{width}}".format("Total", self._size(mem_s.total), width=width) +
                  "\n\t{0:<6}: {1:>{width}}".format("Free", self._size(mem_s.free), width=width) +
                  "\n\t{0:<6}: {1:>{width}} {2}%".format("Used", self._size(mem_s.total - mem_s.free),
                                                         mem_s.percent, width=width))

        # Open files
        open_f = psutil.Process().open_files()
        open_fs = "Open File Handles\n\t"
        if open_f:
            common = os.path.commonpath([f.path for f in open_f])
            if hasattr(open_f[0], "mode"):
                open_fs += "\n\t".join(
                    ["{0} [{1}]".format(f.path.replace(common, '.'), f.mode) for f in open_f])
            else:
                open_fs += "\n\t".join(["{0}".format(f.path.replace(common, '.'))
                                       for f in open_f])
        else:
            open_fs += "None"

        # Disk usage
        disk_u = psutil.disk_usage(os.path.sep)
        width = max([len(self._size(n))
                    for n in [disk_u.total, disk_u.free, disk_u.used]])
        disk_us = ("Disk Usage"
                   "\n\t{0:<6}: {1:>{width}}".format("Total", self._size(disk_u.total), width=width) +
                   "\n\t{0:<6}: {1:>{width}}".format("Free", self._size(disk_u.free), width=width) +
                   "\n\t{0:<6}: {1:>{width}} {2}%".format("Used", self._size(disk_u.used),
                                                          disk_u.percent, width=width))

        # Network
        net_io = psutil.net_io_counters()
        width = max([len(self._size(n))
                    for n in [net_io.bytes_sent, net_io.bytes_recv]])
        net_ios = ("Network"
                   "\n\t{0:<11}: {1:>{width}}".format("Bytes sent", self._size(net_io.bytes_sent), width=width) +
                   "\n\t{0:<11}: {1:>{width}}".format("Bytes recv", self._size(net_io.bytes_recv), width=width))

        # Boot time
        boot_s = ("Boot Time"
                  "\n\t{0}".format(datetime.fromtimestamp(
                      psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")))

        e = discord.Embed(title="System Information", color=0x00ff00)
        e.add_field(name="CPU", value=cpu_cs + "\n" +
                    cpu_ps + "\n" + cpu_ts, inline=True)
        e.add_field(name="Memory", value=mem_vs + "\n" + mem_ss, inline=True)
        e.add_field(name="Open Files", value=open_fs, inline=False)
        e.add_field(name="Disk Usage", value=disk_us, inline=True)
        e.add_field(name="Network", value=net_ios, inline=True)
        e.add_field(name="Boot Time", value=boot_s, inline=True)
        return await interaction.response.send_message(embed=e)

    def _size(self, num):
        for unit in ["Bytes", "KB", "MB", "GB", "TB", "PB", "EB", "ZB"]:
            if abs(num) < 1024.0:
                return "{0:.1f}{1}".format(num, unit)
            num /= 1024.0
        return "{0:.1f}{1}".format(num, "YB")

    @source.error
    @musicstats.error
    @uptime.error
    @commits.error
    @about.error
    @ping.error
    @reload.error
    @report.error
    @suggest.error
    @invite.error
    @sync.error
    async def send_error(self, interaction: discord.Interaction, error):
        self.bot.logger.error(f"[Core] Error: {error}")
        if isinstance(error, commands.MissingPermissions):
            return await interaction.response.send_message("You do not have the required permissions to use this command!", ephemeral=True)
        if isinstance(error, commands.MissingRequiredArgument):
            return await interaction.response.send_message("You are missing a required argument!", ephemeral=True)
        if isinstance(error, commands.BadArgument):
            return await interaction.response.send_message("You provided an invalid argument!", ephemeral=True)
        if isinstance(error, commands.CommandInvokeError):
            return await interaction.response.send_message("An error occurred while running this command!", ephemeral=True)
        else:
            e = discord.Embed(title="An Error has Occurred!",
                              colour=discord.Colour.red())
            e.add_field(name="Error:", value=error)
            try:
                await interaction.response.send_message(embed=e)
            except:
                await interaction.followup.send(embed=e)

    async def use_file_check(self, interaction: discord.Interaction, size: int) -> bool:
        return all([
            size < 50_000, not Flags.FORCE_PAGINATOR,
            (
                not interaction.user.is_on_mobile()
                if interaction.guild and self.bot.intents.presences and isinstance(interaction.user, discord.Member)
                else True
            )
        ])

    async def mean_stddev(self, collection: typing.Collection[float]) -> typing.Tuple[float, float]:
        average = sum(collection) / len(collection)
        if len(collection) > 1:
            stddev = math.sqrt(sum(math.pow(reading - average, 2)
                               for reading in collection) / (len(collection) - 1))
        else:
            stddev = 0.0
        return (average, stddev)


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(Core(bot))
