import math
import discord
import requests
import datetime
from discord.ext import commands
from discord import app_commands as Fresh


class Utility(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    @Fresh.command(name="iplookup")
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

    @Fresh.command(name="weather")
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

    Emoji = Fresh.Group(
        name="emoji", description="All emoji related commands.")

    @Emoji.command(name="steal")
    @Fresh.checks.has_permissions(manage_guild=True)
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


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(Utility(bot))
