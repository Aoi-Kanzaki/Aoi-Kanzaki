import discord
import random
import urllib
import json
from aiohttp import request
from discord.ext import commands
from discord import app_commands as Aoi

from buttons.MemeButtons import MemeButtons


class Fun(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    @Aoi.command(name="phcomment")
    @Aoi.describe(comment="The comment you want to post on PornHub.")
    async def phcomment(self, interaction: discord.Interaction, comment: str):
        """Send a comment on PornHub. ( ͡° ͜ʖ ͡°)"""
        url = f"https://nekobot.xyz/api/imagegen?type=phcomment&image={interaction.user.avatar.url}&username={interaction.user.name}&text={comment}"
        async with request("GET", url) as response:
            json = await response.json()
            if json["status"] == 200:
                e = discord.Embed(color=discord.Colour.teal())
                e.set_image(url=json["message"])
                await interaction.response.send_message(embed=e)
            else:
                await interaction.response.send_message(f"{json['message']}")

    @Aoi.command(name="rps")
    @Aoi.describe(choice="Choose rock, paper, or scissors.")
    async def rps(self, interaction: discord.Interaction, choice: str):
        """Play rock paper scissors with the bot."""
        choices = ["rock", "paper", "scissors"]
        botChoice = random.choice(choices)
        if choice.lower() in choices:
            if choice.lower() == botChoice:
                await interaction.response.send_message(f"You both chose {choice.lower()}, it's a tie!")
            elif choice.lower() in "rock":
                if botChoice == "paper":
                    await interaction.response.send_message(f"I chose {botChoice}, you lose!")
                else:
                    await interaction.response.send_message(f"I chose {botChoice}, you win!")
            elif choice.lower() == "paper":
                if botChoice == "scissors":
                    await interaction.response.send_message(f"I chose {botChoice}, you lose!")
                else:
                    await interaction.response.send_message(f"I chose {botChoice}, you win!")
            elif choice.lower() == "scissors":
                if botChoice == "rock":
                    await interaction.response.send_message(f"I chose {botChoice}, you lose!")
                else:
                    await interaction.response.send_message(f"I chose {botChoice}, you win!")
        else:
            await interaction.response.send_message("Invalid choice, please choose rock, paper, or scissors.")

    @Aoi.command(name="dadjoke")
    async def dadjoke(self, interaction: discord.Interaction):
        """Get a random dad joke."""
        url = "https://dad-jokes.p.rapidapi.com/random/joke"
        headers = {
            "X-RapidAPI-Key": "ef73cad338msh002fd3975548b99p1f8db4jsna8c2f9e965d1",
            "X-RapidAPI-Host": "dad-jokes.p.rapidapi.com",
        }
        async with request("GET", url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                e = discord.Embed(color=discord.Colour.teal())
                e.title = "Here is your dad joke:"
                e.description = f"{data['body'][0]['setup']}\n\n||{data['body'][0]['punchline']}||"
                e.set_thumbnail(url="https://megaphone.imgix.net/podcasts/f9b00b92-4953-11ec-bbeb-6b1d62ae44a1/image/1619957732809-podcast_icon_v2.png?ixlib=rails-2.1.2&max-w=3000&max-h=3000&fit=crop&auto=format,compress?crop=1:1,offset-y0")
                await interaction.response.send_message(embed=e)
            else:
                await interaction.response.send_message(f"{response.status}")

    @Aoi.command(name="meme")
    async def meme(self, interaction: discord.Interaction):
        """You want memes???"""
        memeApi = urllib.request.urlopen(
            "https://meme-api.herokuapp.com/gimme")
        memeData = json.load(memeApi)
        memeUrl = memeData["url"]
        memeName = memeData["title"]
        memeAuthor = memeData["author"]
        memeSub = memeData["subreddit"]
        memeLink = memeData["postLink"]
        e = discord.Embed(title=memeName)
        e.set_image(url=memeUrl)
        e.set_footer(
            text=f"Meme By: {memeAuthor} | Subreddit: {memeSub} | Post: {memeLink}")
        view = MemeButtons()
        view.message = await interaction.channel.send(embed=e, view=view)

    @phcomment.error
    @rps.error
    @dadjoke.error
    @meme.error
    async def send_error(self, interaction: discord.Interaction, error):
        e = discord.Embed(title="An Error has Occurred!",
                          colour=discord.Colour.red())
        e.add_field(name="Error:", value=error)
        try:
            await interaction.response.send_message(embed=e)
        except:
            await interaction.followup.send(embed=e)


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(Fun(bot))
