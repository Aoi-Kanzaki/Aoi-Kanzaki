import discord
import json
import urllib
import random
from aiohttp import request
from discord.ext import commands
from discord import app_commands as Fresh
from decimal import Decimal, ROUND_HALF_UP

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @Fresh.command(name="ship")
    @Fresh.describe(lover1="The user you want to ship.")
    @Fresh.describe(lover2="The user you want to ship lover1 to.")
    async def ship(self, interaction: discord.Interaction, lover1: discord.Member, lover2: discord.Member = None):
        """Ship 2 users."""
        lover2 = lover2 or interaction.user
        rigged = False
        name1 = lover1.name[: -round(len(lover1.name) / 2)] + lover2.name[-round(len(lover2.name) / 2) :]
        name2 = lover2.name[: -round(len(lover2.name) / 2)] + lover1.name[-round(len(lover1.name) / 2) :]
        if 827940585201205258 in [lover1.id, lover2.id] and 882012969523884072 in [lover1.id, lover2.id]:
            rigged = True
        desc = (
            f"**{interaction.user.mention} ships {lover1.mention} and {lover2.mention}!**\n\n "
            f"Ship names: __**{name1}**__ or __**{name2}**__\n\n "
            f"{self.draw_meter(rigged)}"
        )
        e = discord.Embed(description=desc, color=discord.Color.blurple())
        return await interaction.response.send_message(embed=e)

    @Fresh.command(name="phcomment")
    @Fresh.describe(comment="The comment you want to post on PornHub.")
    async def phcomment(self, interaction: discord.Interaction, comment: str):
        """Send a comment on PornHub. ( ͡° ͜ʖ ͡°)"""
        url = f"https://nekobot.xyz/api/imagegen?type=phcomment&image={interaction.user.avatar.url}&username={interaction.user.name}&text={comment}"
        async with request("GET", url) as response:
            json = await response.json()
            if json["status"] == 200:
                e = discord.Embed(color=discord.Color.blurple())
                e.set_image(url=json["message"])
                await interaction.response.send_message(embed=e)
            else:
                await interaction.response.send_message(f"{json['message']}")

    @Fresh.command(name="rps")
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

    @Fresh.command(name="8ball")
    async def _8ball(self, interaction: discord.Interaction, question: str):
        """Ask the 8ball a question."""
        responses = [
            "It is certain.",
            "It is decidedly so.",
            "Without a doubt.",
            "Yes - definitely.",
            "You may rely on it.",
            "As I see it, yes.",
            "Most likely.",
            "Outlook good.",
            "Yes.",
            "Signs point to yes.",
            "Reply hazy, try again.",
            "Ask again later.",
            "Better not tell you now.",
            "Cannot predict now.",
            "Concentrate and ask again.",
            "Don't count on it.",
            "My reply is no.",
            "My sources say no.",
            "Outlook not so good.",
            "Very doubtful.",
        ]
        await interaction.response.send_message(f"Question: {question}\nAnswer: {random.choice(responses)}")

    @Fresh.command(name="dadjoke")
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
                e = discord.Embed(color=discord.Color.blurple())
                e.title = "Here is your dad joke:"
                e.description = f"{data['body'][0]['setup']}\n\n||{data['body'][0]['punchline']}||"
                e.set_thumbnail(url="https://megaphone.imgix.net/podcasts/f9b00b92-4953-11ec-bbeb-6b1d62ae44a1/image/1619957732809-podcast_icon_v2.png?ixlib=rails-2.1.2&max-w=3000&max-h=3000&fit=crop&auto=format,compress?crop=1:1,offset-y0")
                await interaction.response.send_message(embed=e)
            else:
                await interaction.response.send_message(f"{response.status}")

    @Fresh.command(name="meme")
    async def meme(self, interaction: discord.Interaction):
        """You want memes???"""
        memeApi = urllib.request.urlopen("https://meme-api.herokuapp.com/gimme")
        memeData = json.load(memeApi)
        memeUrl = memeData["url"]
        memeName = memeData["title"]
        memeAuthor = memeData["author"]
        memeSub = memeData["subreddit"]
        memeLink = memeData["postLink"]
        e = discord.Embed(title=memeName)
        e.set_image(url=memeUrl)
        e.set_footer(text=f"Meme By: {memeAuthor} | Subreddit: {memeSub} | Post: {memeLink}")
        await interaction.response.send_message(embed=e)

    @staticmethod
    def draw_meter(rigged: bool = False):
        random_integer = 100 if rigged else random.randint(0, 100)
        love = Decimal(str(random_integer / 10)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        love_emoji = "❤"
        empty_bar = "🖤"
        if random_integer == 0:
            empty_bar = "💔"
            love_message = "That's not good... maybe delete this and try again before they see?"
        elif random_integer <= 15:
            love_message = "That's a yikes.."
        elif random_integer <= 30:
            love_message = "Maybe in the future?"
        elif random_integer <= 45:
            love_message = "I mean this is the perfect range for friends?"
        elif random_integer <= 60:
            love_message = "Maybe try talking more?"
        elif random_integer == 69:
            love_emoji = "😏"
            love_message = "That's the sex number *wink wonk*"
        elif random_integer <= 75:
            love_message = "Best friends, stay as best friends."
        elif random_integer <= 90:
            love_message = "Give it a go, you're made for each other!"
        elif random_integer <= 99:
            love_message = "I ship it!"
        else:
            love_emoji = "💙"
            love_message = "Go get married! I hope I'm invited ❤"
        bar = "".join(love_emoji if i < love else empty_bar for i in range(10))
        return f"**Love meter:** {bar} **{random_integer}%**\n**{love_message}**"

async def setup(bot):
    await bot.add_cog(Fun(bot))