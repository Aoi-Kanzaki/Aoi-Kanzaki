import os
import discord
import requests
import datetime
import python_weather
from discord.ext import commands
from discord import app_commands as Fresh


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @Fresh.command(name="iplookup")
    async def iplookup(self, interaction: discord.Interaction, ipaddr: str = "9.9.9.9"):
        """Lookup an ip address."""
        r = requests.get(
            f"http://extreme-ip-lookup.com/json/{ipaddr}?key=BnhTX1mBfAK0y9v1gtvh")
        geo = r.json()
        e = discord.Embed(color=discord.Color.blurple())
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
        weather = await self.get_weather(city)
        e = discord.Embed(color=discord.Color.blurple())
        for forecast in weather.forecasts:
            value = ""
            for hourly in forecast.hourly:
                value += f"`{hourly.time}` - {hourly.description} with a temp of {hourly.temperature}°F\n"
            e.add_field(name=f"{forecast.date}", value=value, inline=False)
        await interaction.response.send_message(embed=e)

    async def get_weather(self, city: str):
        async with python_weather.Client(format=python_weather.IMPERIAL) as client:
            weather = await client.get(city)
            return weather


async def setup(bot):
    await bot.add_cog(Utility(bot))
