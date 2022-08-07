import os
import pathlib
import codecs
import sys
import json
import psutil
import humanize
import discord
import aiosqlite
import requests
import datetime
import python_weather
from colr import color
from discord.ext import commands

class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @bot.tree.context_menu(name="Retrieve Avatar")
        async def get_avatar(interaction: discord.Interaction, member: discord.Member):
            e = discord.Embed(color=discord.Color.blurple())
            e.title = f"{member.name}'s Avatar:"
            e.set_image(url=member.avatar.url)
            await interaction.response.send_message(embed=e)

        @bot.tree.context_menu(name='Report to Moderators')
        async def report_message(interaction: discord.Interaction, message: discord.Message):
            if interaction.guild.id != 678226695190347797:
                return await interaction.response.send_message("This doesn't work outside of Jonny's server!", ephemeral=True)
            await interaction.response.send_message(
                f'Thanks for reporting this message by {message.author.mention} to our moderators.', ephemeral=True
            )
            log_channel = interaction.guild.get_channel(995171906426773564)
            embed = discord.Embed(title='Reported Message')
            if message.content:
                embed.description = message.content
            embed.set_author(name=message.author.display_name, icon_url=message.author.display_avatar.url)
            embed.timestamp = message.created_at
            url_view = discord.ui.View()
            url_view.add_item(discord.ui.Button(label='Go to Message', style=discord.ButtonStyle.url, url=message.jump_url))
            await log_channel.send(embed=embed, view=url_view)

    async def cog_load(self):
        async with aiosqlite.connect("./data/afk.db") as db:
            await db.execute("CREATE TABLE IF NOT EXISTS afk (user INTEGER, guild INTEGER, reason TEXT)")
            await db.commit()
        print(color("The utility cog is ready!", fore=self.bot.colors['blue']))

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.guild is None:
            return
        if message.author.bot:
            return
        async with aiosqlite.connect("./data/afk.db") as db:
            get_data = await db.execute("SELECT reason FROM afk WHERE user = ? AND guild = ?", (message.author.id, message.guild.id,))
            data = await get_data.fetchone()
            if data:
                await message.channel.send(f"{message.author.mention} Welcome back! You are no longer afk.", delete_after=10)
                await db.execute("DELETE FROM afk WHERE user = ? AND guild = ?", (message.author.id, message.guild.id,))
            if message.mentions:
                for mention in message.mentions:
                    get_data = await db.execute("SELECT reason FROM afk WHERE user = ? AND guild = ?", (mention.id, message.guild.id,))
                    data = await get_data.fetchone()
                    if data and mention.id != message.author.id:
                        await message.channel.send(f"{mention.name} is currently AFK! Reason: `{data[0]}`", delete_after=10)
            await db.commit()

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        with open('./data/voice_leaderboard.json', 'r') as file:
            voice_data = json.load(file)
            new_user = str(member.id)
        if new_user in voice_data:
            voice_leave_time = datetime.datetime.now().time().strftime('%H:%M:%S')
            voice_join_time = voice_data[new_user]
            calculate_time = (
                    datetime.datetime.strptime(voice_leave_time, '%H:%M:%S') - datetime.datetime.strptime(
                voice_join_time, '%H:%M:%S'))
            voice_data[new_user] = f'{calculate_time}'
            with open('./data/voice_leaderboard.json', 'w') as update_user_data:
                json.dump(voice_data, update_user_data, indent=4)
        else:
            new_voice_join_time = datetime.datetime.now().time().strftime('%H:%M:%S')
            voice_data[new_user] = new_voice_join_time
            with open('./data/voice_leaderboard.json', 'w') as new_user_data:
                json.dump(voice_data, new_user_data, indent=4)

    @commands.command()
    async def voice(self, ctx):
        with open('./data/voice_leaderboard.json', 'r') as file:
            voice_data = json.load(file)
            if not voice_data:
                return await ctx.send("Oops, seems like there is no voice stats data file? Try again later.")
            elif not voice_data[str(ctx.author.id)]:
                return await ctx.send("Oops, seems like you have not joined any voice channels yet? Try again later.")
            else:
                tmsg = ""
                if ctx.author.voice is not None:
                    calculate_time = (
                    datetime.datetime.strptime(datetime.datetime.now().time().strftime('%H:%M:%S'), '%H:%M:%S') - datetime.datetime.strptime(
                    voice_data[str(ctx.author.id)], '%H:%M:%S'))
                    ctime = str(calculate_time).split(':')
                    if ctime[0] != '0':
                        if int(ctime[0]) > 1:
                            e = 'hours'
                        else:
                            e = 'hour'
                        tmsg += f"{ctime[0]} {e}, "
                    if ctime[1] != '00':
                        if int(ctime[1]) > 1:
                            e = 'minutes'
                        else:
                            e = 'mibnute'
                        tmsg += f"{ctime[1]} {e} and "
                    if ctime[2] != '0':
                        tmsg += f"{ctime[2]} seconds"
                else:
                    time = voice_data[str(ctx.author.id)].split(':')
                    if time[0] != '0':
                        if int(time[0]) > 1:
                            e = 'hours'
                        else:
                            e = 'hour'
                        tmsg += f"{time[0]} {e}, "
                    if time[1] != '00':
                        if int(time[1]) > 1:
                            e = 'minutes'
                        else:
                            e = 'mibnute'
                        tmsg += f"{time[1]} {e} and "
                    if time[2] != '0':
                        tmsg += f"{time[2]} seconds"
                return await ctx.send(f"You have spent a total of `{tmsg}` in voice channels.")

    @commands.command()
    async def afk(self, ctx, *, reason=None):
        """Go afk with a personal message."""
        if reason is None:
            reason = "No reason provided."
        async with aiosqlite.connect("./data/afk.db") as db:
            try:
                get_data = await db.execute("SELECT reason FROM afk WHERE user = ? AND guild = ?", (ctx.author.id, ctx.guild.id,))
                data = await get_data.fetchone()
            except: pass
            if data:
                if data[0] == reason:
                    await ctx.send("You're already AFK with the same reason.")
                await db.execute("UPDATE afk SET reason = ? WHERE user = ? AND guild = ?", (reason, ctx.author.id, ctx.guild.id,))
            else:
                await db.execute("INSERT INTO afk (user, guild, reason) VALUES (?, ?, ?)", (ctx.author.id, ctx.guild.id, reason,))
                await ctx.send(f"You are now AFK for: `{reason}`")
            await db.commit()

    @commands.command()
    async def iplookup(self, ctx, *, ipaddr: str='9.9.9.9'):
        """Lookup an ip address."""
        r = requests.get(f"http://extreme-ip-lookup.com/json/{ipaddr}?key=BnhTX1mBfAK0y9v1gtvh")
        geo = r.json()
        e = discord.Embed(color=discord.Color.blurple())
        fields = [
            {'name': 'IP', 'value': geo['query']},
            {'name': 'IP Type', 'value': geo['ipType']},
            {'name': 'Country', 'value': geo['country']},
            {'name': 'City', 'value': geo['city']},
            {'name': 'Continent', 'value': geo['continent']},
            {'name': 'IP Name', 'value': geo['ipName']},
            {'name': 'ISP', 'value': geo['isp']},
            {'name': 'Latitude', 'value': geo['lat']},
            {'name': 'Longitude', 'value': geo['lon']},
            {'name': 'Org', 'value': geo['org']},
            {'name': 'Region', 'value': geo['region']},
            {'name': 'Status', 'value': geo['status']},
        ]
        for field in fields:
            if field['value']:
                e.add_field(name=field['name'], value=field['value'], inline=True)
        e.set_footer(text="\u200b")
        e.timestamp = datetime.datetime.utcnow()
        return await ctx.send(embed=e)

    @commands.command()
    async def commits(self, ctx):
        """Shows last 5 github commits."""
        cmd = r'git show -s HEAD~5..HEAD --format="[{}](https://github.com/JonnyBoy2000/Fresh/commit/%H) %s (%cr)"'
        if os.name == 'posix':
            cmd = cmd.format(r'\`%h\`')
        else:
            cmd = cmd.format(r'`%h`')
        try:
            revision = os.popen(cmd).read().strip()
        except OSError:
            revision = 'Could not fetch due to memory error. Sorry.'
        e = discord.Embed()
        e.colour = discord.Colour.blurple()
        e.description = revision
        e.set_author(icon_url=self.bot.user.avatar, name="Latest Github Changes:")
        e.set_thumbnail(url="https://avatars2.githubusercontent.com/u/22266893?s=400&u=9df85f1c8eb95b889fdd643f04a3144323c38b66&v=4")
        await ctx.send(embed=e)

    @commands.command(aliases=['lls'])
    async def stats(self, ctx):
        """Posts bot stats."""
        await ctx.typing()
        oe = "<:online:1001425556887326720>"
        ie = "<:idle:1001425440734466098>"
        de = "<:dnd:1001425507331625060>"
        cpuUsage      = psutil.cpu_percent(interval=1)
        cpuThred      = os.cpu_count()
        threadString = 'thread'
        if not cpuThred == 1:
            threadString += 's'
        memStats      = psutil.virtual_memory()
        memUsed       = memStats.used
        memTotal      = memStats.total
        memUsedGB     = "{0:.1f}".format(((memUsed / 1024) / 1024) / 1024)
        memTotalGB    = "{0:.1f}".format(((memTotal/1024)/1024)/1024)
        memPerc       = str(((memTotal/1024)/1024)/1024 / ((memUsed / 1024) / 1024) / 1024).split('.')[0]
        online = len([e.name for e in self.bot.get_all_members() if e.status == discord.Status.online])
        idle = len([e.name for e in self.bot.get_all_members() if e.status == discord.Status.idle])
        dnd = len([e.name for e in self.bot.get_all_members() if e.status == discord.Status.dnd])
        used = humanize.naturalsize(psutil.virtual_memory().used)
        free = humanize.naturalsize(psutil.virtual_memory().free)
        memory = f"**Used:** {used}\n"
        memory += f"**Free:** {free}\n"
        cpu = f"**Cores:** {os.cpu_count()}\n"
        cpu += '**Cpu:** {}% of ({} {}) utilized\n'.format(cpuUsage, cpuThred, threadString)
        cpu += '**Ram:** {} ({}%) of {}GB used\n'.format(memUsedGB, memPerc, memTotalGB)
        members = f"{oe} {online} users online.\n"
        members += f"{ie} {idle} users idle.\n"
        members += f"{de} {dnd} users dnd."
        vcs = 0
        tcs = 0
        for guild in self.bot.guilds:
            for channel in guild.text_channels:
                tcs += 1
            for channel in guild.voice_channels:
                vcs += 1
        channels = f"{vcs} Voice Channels\n{tcs} Text Channels"
        e = discord.Embed()
        e.colour = discord.Colour.blurple()
        e.set_author(name=f"{self.bot.user.name} Stats:", icon_url=self.bot.user.avatar)
        e.add_field(name="Guilds:", value=f"{len(self.bot.guilds)} Guilds\n{channels}")
        e.add_field(name="Members:", value=members)
        e.add_field(name="Memory:", value=memory)
        e.add_field(name="CPU | RAM:", value=cpu)
        e.add_field(name="Uptime:", value=f"{self.get_bot_uptime()}", inline=False)
        e.set_thumbnail(url=self.bot.user.avatar)
        await ctx.send(embed=e)

    @commands.hybrid_group()
    async def info(self, ctx):
        """Info commands."""
        if ctx.invoked_subcommand is None or isinstance(ctx.invoked_subcommand, commands.Group):
            await self.bot.send_sub_help(ctx, ctx.command)

    @info.command()
    async def lavalink(self, ctx):
        """Shows lavalink music stats."""
        server_num = self.get_playing()
        server_ids = self.bot.lavalink.player_manager.players
        server_list = []
        number = 0
        users = 0
        await ctx.typing()
        for _id, p in server_ids.items():
            try:
                if p.is_playing:
                    number += 1
                    g = self.bot.get_guild(_id)
                    users += len(g.me.voice.channel.members)
                    server_list.append(f"`{number}.` {g.name}: **{p.current.title}**")
            except AttributeError:
                pass
        if server_list == []:
            servers = 'Not connected anywhere.'
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
            return await ctx.send(embed=e)
        except discord.HTTPException:
            e = discord.Embed(colour=discord.Colour.blurple())
            e.description = f"**Well aren't we just popular? I can't display all the servers. But I am currently playing in {server_num} servers.**"
            return await ctx.send(embed=e)

    @info.command()
    async def bot(self, ctx):
        """Shows basic info about the bot."""
        total = 0
        file_amount = 0
        pyvi = sys.version_info
        discordi = f"Discord.py: v{discord.__version__} (Branch rewrite)"
        python = f"Python: v{pyvi.major}.{pyvi.minor}.{pyvi.micro} (Branch {pyvi.releaselevel} v{pyvi.serial})"
        dev = await self.bot.http.get_user(827940585201205258)
        devn = f"{dev['username']}#{dev['discriminator']}"
        for path, subdirs, files in os.walk('.'):
            for name in files:
                if name.endswith('.py'):
                    file_amount += 1
                    with codecs.open('./' + str(pathlib.PurePath(path, name)), 'r', 'utf-8') as f:
                        for i, l in enumerate(f):
                            if l.strip().startswith('#') or len(l.strip()) == 0:  # skip commented lines.
                                pass
                            else:
                                total += 1
        code = f'I am made of {total:,} lines of Python, spread across {file_amount:,} files!'
        cmd = r'git show -s HEAD~3..HEAD --format="[{}](https://github.com/JonnyBoy2000/Fresh/commit/%H) %s (%cr)"'
        if os.name == 'posix':
            cmd = cmd.format(r'\`%h\`')
        else:
            cmd = cmd.format(r'`%h`')
        try:
            revision = os.popen(cmd).read().strip()
        except OSError:
            revision = 'Could not fetch due to memory error. Sorry.'
        e = discord.Embed()
        e.colour = discord.Colour.blurple()
        e.add_field(name="Developer:", value=devn)
        e.add_field(name="Libraries:", value=f"{discordi}\n{python}")
        e.add_field(name="Latest Changes:", value=revision, inline=False)
        e.add_field(name="Code Information:", value=code)
        e.set_author(name=f"F.res.h {self.bot.version}", icon_url=ctx.author.avatar)
        e.set_thumbnail(url=self.bot.user.avatar)
        await ctx.send(embed=e)

    @info.command()
    async def user(self, ctx, user: discord.Member=None):
        """Information about your account or someone elses."""
        if user is None:
            user = ctx.author
        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(name="Name", value=user.name)
        embed.add_field(name="ID", value=user.id)
        embed.add_field(name="Status", value=user.status)
        embed.add_field(name="Highest role", value=user.top_role.mention)
        embed.add_field(name="Created", value=user.created_at.strftime("%A, %B %d %Y @ %H:%M:%S %p"), inline=False)
        embed.add_field(name="Joined", value=user.joined_at.strftime("%A, %B %d %Y @ %H:%M:%S %p"), inline=False)
        embed.set_thumbnail(url=user.avatar)
        await ctx.send(embed=embed)

    @info.command(aliases=['server'])
    async def guild(self, ctx):
        """Information on the guild/server."""
        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(name="Name", value=ctx.guild.name)
        embed.add_field(name="Owner", value=ctx.guild.owner.mention)
        embed.add_field(name="Members", value=ctx.guild.member_count)
        embed.add_field(name="Channels", value=len(ctx.guild.channels))
        embed.add_field(name="Created", value=ctx.guild.created_at.strftime("%A, %B %d %Y @ %H:%M:%S %p"), inline=False)
        embed.add_field(name="Roles", value=", ".join([e.mention for e in ctx.guild.roles]), inline=False)
        embed.set_thumbnail(url=ctx.guild.icon)
        await ctx.send(embed=embed)

    @info.command()
    async def role(self, ctx, role: discord.Role):
        """Information on a server role."""
        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(name="Name", value=role.name)
        embed.add_field(name="ID", value=role.id)
        embed.add_field(name="Color", value=role.colour)
        embed.add_field(name="Position", value=role.position)
        embed.add_field(name="Hoist", value=role.hoist)
        embed.add_field(name="Mentionable", value=role.mentionable)
        embed.add_field(name="Created", value=role.created_at.strftime("%A, %B %d %Y @ %H:%M:%S %p"), inline=False)
        embed.set_thumbnail(url=role.guild.icon)
        await ctx.send(embed=embed)

    @info.command()
    async def textchannel(self, ctx, channel: discord.TextChannel=None):
        """Information on a text channel."""
        if channel is None:
            channel = ctx.channel
        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(name="Name", value=channel.name)
        embed.add_field(name="ID", value=channel.id)
        embed.add_field(name="NSFW", value=channel.is_nsfw())
        embed.add_field(name="Position", value=channel.position)
        embed.add_field(name="Created", value=channel.created_at.strftime("%A, %B %d %Y @ %H:%M:%S %p"), inline=False)
        embed.add_field(name="Topic", value=channel.topic, inline=False)
        embed.set_thumbnail(url=channel.guild.icon)
        await ctx.send(embed=embed)

    @info.command()
    async def voicechannel(self, ctx, channel: discord.VoiceChannel=None):
        """Information on a voice channel."""
        if channel is None:
            if not ctx.author.voice:
                return await ctx.send("Please pass the name of a voice channel.")
            else:
                channel = ctx.author.voice.channel
        embed = discord.Embed(color=discord.Color.blurple())
        embed.add_field(name="Name", value=channel.name)
        embed.add_field(name="ID", value=channel.id)
        embed.add_field(name="Created", value=channel.created_at.strftime("%A, %B %d %Y @ %H:%M:%S %p"), inline=False)
        embed.set_thumbnail(url=channel.guild.icon)
        await ctx.send(embed=embed)

    @commands.command()
    async def weather(self, ctx, *, city: str):
        """Get your citys weather."""
        weather = await self.get_weather(city)
        e = discord.Embed(color=discord.Color.blurple())
        for forecast in weather.forecasts:
            value = ""
            for hourly in forecast.hourly:
                value += f"`{hourly.time}` - {hourly.description} with a temp of {hourly.temperature}°F\n"
            e.add_field(name=f"{forecast.date}", value=value, inline=False)
        await ctx.send(embed=e)

    @commands.command()
    async def uptime(self, ctx):
        """How long have I been online?"""
        uptime = self.get_bot_uptime()
        await ctx.send(uptime)

    async def get_weather(self, city: str):
        async with python_weather.Client(format=python_weather.IMPERIAL) as client:
            weather = await client.get(city)
            return weather

    def get_playing(self):
        return len([p for p in self.bot.lavalink.player_manager.players.values() if p.is_playing])

    def get_bot_uptime(self, *, brief=False):
        now = datetime.datetime.utcnow()
        delta = now - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)

        if not brief:
            fmt = 'I\'ve been online for {d} days, {h} hours, {m} minutes, and {s} seconds!'
        else:
            fmt = '{d}d {h}h {m}m {s}s'
        return fmt.format(d=days, h=hours, m=minutes, s=seconds)


async def setup(bot):
    await bot.add_cog(Utility(bot))