import time
import math
import discord
import aiohttp
import requests
import datetime
from discord.ext import commands
from discord import app_commands as Aoi


class Utility(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.afk = self.bot.db.afk

    @Aoi.command(name="afk", description="Set an afk status!")
    @Aoi.describe(reason="The reason why you are afk.")
    async def afk(self, interaction: discord.Interaction, reason: str = None):
        """Set an afk status."""
        data = await self.afk.find_one({"_id": interaction.user.id})
        if data is not None:
            await self.afk.delete_one({"_id": interaction.user.id})
            return await interaction.response.send_message(
                "<:tickYes:697759553626046546> Your afk status has been removed!")
        if reason is None:
            reason = "No reason provided."
        await self.afk.insert_one({
            "_id": interaction.user.id,
            "reason": reason
        })
        return await interaction.response.send_message(
            content=f"{interaction.user.mention} is now afk!",
            ephemeral=True
        )

    @Aoi.command(name="activity", description="Get the activity of a user")
    @Aoi.describe(member="The user you want to get the activity of.")
    async def activity(self, interaction: discord.Interaction, member: discord.Member = None):
        await interaction.response.defer()
        embeds = []

        member = member or interaction.user
        member = member.guild.get_member(member.id)

        if member.activities != None:
            for activity in member.activities:
                if isinstance(activity, discord.Spotify):
                    e = discord.Embed(
                        title="Listening to Spotify",
                        colour=activity.color
                    )
                    e.description = f"**Title:** {activity.title}\n"
                    e.description += f"**Artist:** {activity.artist}\n"
                    e.description += f"**Album:** {activity.album}"
                    e.set_thumbnail(url=activity.album_cover_url)
                    embeds.append(e)
                elif isinstance(activity, discord.Activity):
                    e = discord.Embed(
                        title=f"{activity.name}",
                        colour=discord.Colour.blurple()
                    )
                    if activity.details:
                        e.description = f"{activity.details}"
                    if activity.large_image_url:
                        e.set_thumbnail(url=activity.large_image_url)
                    embeds.append(e)
                elif isinstance(activity, discord.CustomActivity):
                    e = discord.Embed(
                        colour=discord.Colour.blurple(),
                        description=activity.name
                    )
                    embeds.append(e)
                elif isinstance(activity, discord.Streaming):
                    e = discord.Embed(
                        colour=discord.Colour.purple(),
                        title="Currently Streaming"
                    )
                    e.description = f"**Platform:** {activity.platform}\n"
                    e.description += f"**Name:** {activity.name}\n"
                    e.description += f"**Game:** {activity.game}\n"
                    e.description += f"Come watch here! [Go to {activity.platform}]({activity.url})"
                    embeds.append(e)
                elif isinstance(activity, discord.Game):
                    e = discord.Embed(
                        colour=discord.Colour.blurple(),
                        description=activity.name
                    )
                    embeds.append(e)

            return await interaction.followup.send(embeds=embeds, content=f"**{member}'s Activities:**")

        return await interaction.followup.send("Nothing found.")

    @Aoi.command(name="userinfo")
    @Aoi.describe(user="The member you want to get information about.")
    async def userinfo(self, interaction: discord.Interaction, user: discord.Member = None):
        """Get a users information."""
        if user is None:
            user = interaction.user
        roles = ", ".join(
            [f"<@&{x.id}>" for x in sorted(user.roles, key=lambda x: x.position,
                                           reverse=True) if x.id != interaction.guild.default_role.id]
        ) if len(user.roles) > 1 else "None"

        e = discord.Embed(colour=user.top_role.color.value)
        e.set_thumbnail(url=user.avatar.url)
        e.add_field(name="Name:", value=user)
        e.add_field(name="Nickname", value=user.nick if hasattr(
            user, "nick") else "None")
        e.add_field(name="ID", value=user.id)
        e.add_field(name=f"Roles ({len(user.roles)-1})",
                    value=roles, inline=False)
        e.add_field(name="Created Account",
                    value=f"<t:{str(time.mktime(user.created_at.timetuple())).split('.')[0]}:R>")
        e.add_field(name="Joined this server",
                    value=f"<t:{str(time.mktime(user.joined_at.timetuple())).split('.')[0]}:R>")

        usr = await self.bot.fetch_user(user.id)
        if usr.banner:
            e.set_image(url=usr.banner.url)
        return await interaction.response.send_message(embed=e)

    @Aoi.command(name="serverinfo")
    async def serverinfo(self, interaction: discord.Interaction):
        """Shows information about the server."""
        bots = sum(1 for member in interaction.guild.members if member.bot)
        e = discord.Embed(colour=discord.Colour.teal(
        ), title=f"**{interaction.guild.name}** ({interaction.guild.id})")
        if interaction.guild.icon:
            e.set_thumbnail(url=interaction.guild.icon)
        if interaction.guild.banner:
            e.set_image(url=interaction.guild.banner.with_format(
                "png").with_size(1024))
        e.add_field(name="Server Name",
                    value=interaction.guild.name)
        e.add_field(
            name="Owner", value=interaction.guild.owner.mention)
        e.add_field(name="Created",
                    value=f"<t:{str(time.mktime(interaction.guild.created_at.timetuple())).split('.')[0]}:R>", inline=False)
        e.add_field(name="Members",
                    value=interaction.guild.member_count)
        e.add_field(name="Bots", value=bots)
        return await interaction.response.send_message(embed=e)

    @Aoi.command(name="iplookup")
    @Aoi.describe(ipaddr="The IP you want to lookup.")
    async def iplookup(self, interaction: discord.Interaction, ipaddr: str = "9.9.9.9"):
        """Lookup an ip address."""
        r = requests.get(
            f"http://extreme-ip-lookup.com/json/{ipaddr}?key=BnhTX1mBfAK0y9v1gtvh")
        geo = r.json()
        e = discord.Embed(color=discord.Colour.teal())
        fields = [
            {"name": "IP", "value": geo["query"]},
            {"name": "IP Type", "value": geo["ipType"]},
            {"name": "Country", "value": geo["country"]},
            {"name": "City", "value": geo["city"]},
            {"name": "Continent", "value": geo["continent"]},
            {"name": "IP Name", "value": geo["ipName"]},
            {"name": "ISP", "value": geo["isp"]},
            {"name": "Latitude", "value": geo["lat"]},
            {"name": "Longitude", "value": geo["lon"]},
            {"name": "Org", "value": geo["org"]},
            {"name": "Region", "value": geo["region"]},
            {"name": "Status", "value": geo["status"]},
        ]
        for field in fields:
            if field["value"]:
                e.add_field(name=field["name"],
                            value=field["value"], inline=True)
        e.set_footer(text="\u200b")
        e.timestamp = datetime.datetime.utcnow()
        return await interaction.response.send_message(embed=e)

    @Aoi.command(name="weather")
    @Aoi.describe(city="The city you want to get the weather for.")
    async def weather(self, interaction: discord.Interaction, city: str):
        """Get your citys weather."""
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={self.bot.config['weatherApiKey']}"
        get = requests.get(url)
        data = get.json()
        e = discord.Embed(colour=discord.Colour.teal())
        e.title = f"Current Weather for {data['name']}"
        e.add_field(name="Current Temp:",
                    value=f"{math.floor((data['main']['temp'] * 1.8) - 459.67)} °F")
        e.add_field(name="Humidity:",
                    value=f"{data['main']['humidity']}%")
        e.add_field(name="Feels Like:",
                    value=f"{math.floor((data['main']['feels_like'] * 1.8) - 459.67)} °F")
        e.add_field(name="Max Temp:",
                    value=f"{math.floor((data['main']['temp_max'] * 1.8) - 459.67)} °F")
        e.add_field(name="Min Temp:",
                    value=f"{math.floor((data['main']['temp_min'] * 1.8) - 459.67)} °F")
        icon_url = f" http://openweathermap.org/img/wn/{data['weather'][0]['icon']}.png"
        e.set_thumbnail(url=icon_url)
        return await interaction.response.send_message(
            embed=e
        )

    Emoji = Aoi.Group(
        name="emoji", description="All emoji related commands.")

    @Emoji.command(name="steal")
    @Aoi.describe(emoji="The emoji you want to steal.")
    @Aoi.checks.has_permissions(manage_guild=True)
    async def steal(self, interaction: discord.Interaction, emoji: str):
        """Steal and emoji and copy it to this server."""
        try:
            foundEmoji = self.bot.get_emoji(int(emoji.split(":")[2][0:-1]))
            if foundEmoji is None:
                return await interaction.response.send_message(
                    content="I couldn't find that emoji! Please make sure it's in a server I'm in."
                )
            else:
                copiedEmoji = await interaction.guild.create_custom_emoji(
                    name=foundEmoji.name,
                    image=await foundEmoji.read()
                )
                return await interaction.response.send_message(
                    content=f"I have copied the emoji! {copiedEmoji}"
                )
        except Exception as e:
            return await interaction.response.send_message(
                content=e,
                ephemeral=True
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot:
            return
        data = await self.afk.find_one({"_id": message.author.id})
        if data is not None:
            await self.afk.delete_one({"_id": message.author.id})
            return await message.channel.send(
                f"{message.author.mention}  welcome back, I have removed your afk status!")
        if message.mentions:
            for user in message.mentions:
                if await self.afk.find_one({"_id": user.id}):
                    data = await self.afk.find_one({"_id": user.id})
                    e = discord.Embed(
                        color=discord.Color.blurple()
                    )
                    e.set_author(name=f"{user.name} is afk!",
                                 icon_url=user.avatar)
                    e.add_field(name="Reason:", value=data['reason'])
                    return await message.channel.send(embed=e)

    @steal.error
    @weather.error
    @iplookup.error
    @serverinfo.error
    @userinfo.error
    @activity.error
    @afk.error
    async def send_error(self, interaction: discord.Interaction, error):
        self.bot.logger.error(f"[Utility] Error: {error}")
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
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(
                    url=self.bot.config['webhooks']['mainlogs'], session=session)
                await webhook.send(embed=e)


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(Utility(bot))
