import discord
import datetime
import aiohttp
from discord.ext import commands, tasks


class AoiLogging(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.update_status_message.start()

    @commands.Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        totalMembers = len([e for e in self.bot.get_all_members()])
        e = discord.Embed(colour=discord.Colour.green())
        e.set_author(
            name=f"Joined Guild {guild.name}", icon_url=self.bot.user.avatar)
        e.set_thumbnail(url=guild.icon)
        e.add_field(name="Guild Owner:", value=guild.owner.name)
        e.add_field(name="Guild ID:", value=guild.id)
        members = len([e for e in guild.members if not e.bot])
        bots = len([e for e in guild.members if e.bot])
        e.add_field(
            name="Members:", value=f"There is currently **{members} members** and **{bots} bots** in this guild!", inline=False)
        e.add_field(name="# of Guilds:",
                    value=f"Aoi is now in **{len(self.bot.guilds)}** guilds with **{totalMembers} users**!", inline=False)
        e.timestamp = datetime.datetime.now()
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(
                url=self.bot.config['webhooks']['mainlogs'], session=session)
            await webhook.send(embed=e)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        totalMembers = len([e for e in self.bot.get_all_members()])
        e = discord.Embed(colour=discord.Colour.orange())
        e.set_author(name=f"Left {guild.name}", icon_url=self.bot.user.avatar)
        e.set_thumbnail(url=guild.icon)
        e.add_field(name="Guild Owner:", value=guild.owner.name)
        e.add_field(name="Guild ID:", value=guild.id)
        e.add_field(name="# of Guilds:",
                    value=f"Aoi is now in **{len(self.bot.guilds)}** guilds with **{totalMembers} users**!", inline=False)
        e.timestamp = datetime.datetime.now()

        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(
                url=self.bot.config['webhooks']['mainlogs'], session=session)
            await webhook.send(embed=e)

    @commands.Cog.listener()
    async def on_application_command_error(self, interaction: discord.Interaction, error):
        if isinstance(error, commands.MissingPermissions):
            return
        else:
            e = discord.Embed(color=discord.Colour.red())
            e.set_author(name="Aoi Error Logs", icon_url=self.bot.user.avatar)
            e.set_thumbnail(url=interaction.guild.icon)
            e.add_field(name="Guild:", value=interaction.guild.name)
            e.add_field(name="Command:", value=interaction.command.name)
            e.add_field(
                name="Author:", value=f"Command was ran by {interaction.user}({interaction.user.id}).", inline=False)
            e.add_field(name="Error:",
                        value=f"```py\n{error}```", inline=False)
            e.timestamp = datetime.datetime.now()

        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(
                url=self.bot.config['webhooks']['mainlogs'], session=session)
            await webhook.send(embed=e)

    @tasks.loop(minutes=10)
    async def update_status_message(self):
        uptime = self.get_bot_uptime()

        e = discord.Embed(colour=discord.Colour.teal())
        e.set_author(name="Aoi Status", icon_url=self.bot.user.avatar)
        e.add_field(name="Response Time:",
                    value=f'{round(self.bot.latency * 1000)}ms')
        e.add_field(name="Commands Ran:", value=self.bot.commandsRan)
        e.add_field(name="Database:",
                    value="Connected, and fully functional.", inline=False)
        e.add_field(
            name="Uptime:", value=uptime, inline=False)
        e.set_thumbnail(url=self.bot.user.avatar)
        e.timestamp = datetime.datetime.now()
        e.set_footer(text="Last updated")

        channel = await self.bot.fetch_channel(1045203380517208114)
        msg = await channel.fetch_message(1045204532692533338)

        return await msg.edit(content=None, embed=e)

    def get_bot_uptime(self, *, brief=False):
        now = datetime.datetime.utcnow()
        delta = now - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        if not brief:
            fmt = "{d} days, {h} hours, {m} minutes, and {s} seconds!"
        else:
            fmt = "{d}d {h}h {m}m {s}s"
        return fmt.format(d=days, h=hours, m=minutes, s=seconds)


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(AoiLogging(bot))
