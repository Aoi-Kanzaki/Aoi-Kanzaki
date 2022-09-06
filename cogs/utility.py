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
        r = requests.get(f"http://extreme-ip-lookup.com/json/{ipaddr}?key=BnhTX1mBfAK0y9v1gtvh")
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
                e.add_field(name=field["name"], value=field["value"], inline=True)
        e.set_footer(text="\u200b")
        e.timestamp = datetime.datetime.utcnow()
        return await interaction.response.send_message(embed=e)

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
        e.set_author(icon_url=self.bot.user.avatar, name="Latest Github Changes:")
        e.set_thumbnail(url="https://avatars2.githubusercontent.com/u/22266893?s=400&u=9df85f1c8eb95b889fdd643f04a3144323c38b66&v=4")
        await interaction.response.send_message(embed=e)

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

    @Fresh.command(name="uptime")
    async def uptime(self, interaction: discord.Interaction):
        """Shows the uptime of the bot."""
        uptime = uptime = self.get_bot_uptime()
        await interaction.response.send_message(uptime)

    async def get_weather(self, city: str):
        async with python_weather.Client(format=python_weather.IMPERIAL) as client:
            weather = await client.get(city)
            return weather

    def get_bot_uptime(self, *, brief=False):
        now = datetime.datetime.utcnow()
        delta = now - self.bot.uptime
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        if not brief:
            fmt = "I've been online for {d} days, {h} hours, {m} minutes, and {s} seconds!"
        else:
            fmt = "{d}d {h}h {m}m {s}s"
        return fmt.format(d=days, h=hours, m=minutes, s=seconds)

async def setup(bot):
    await bot.add_cog(Utility(bot))