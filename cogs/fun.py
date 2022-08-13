import discord
import json
import urllib
import random
from aiohttp import request
from discord.ext import commands
from decimal import Decimal, ROUND_HALF_UP

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def meme(self, ctx):
        """You want memes???"""
        await ctx.typing()
        memeApi = urllib.request.urlopen("https://meme-api.herokuapp.com/gimme")
        memeData = json.load(memeApi)
        memeUrl = memeData['url']
        memeName = memeData['title']
        memeAuthor = memeData['author']
        memeSub = memeData['subreddit']
        memeLink = memeData['postLink']
        e = discord.Embed(title=memeName)
        e.set_image(url=memeUrl)
        e.set_footer(text=f"Meme By: {memeAuthor} | Subreddit: {memeSub} | Post: {memeLink}")
        await ctx.send(embed=e)

    @commands.hybrid_command(aliases=['dj'])
    async def dadjoke(self, ctx):
        """Get a random dad joke."""
        await ctx.typing()
        url = "https://dad-jokes.p.rapidapi.com/random/joke"
        headers = {
            "X-RapidAPI-Key": "ef73cad338msh002fd3975548b99p1f8db4jsna8c2f9e965d1",
            "X-RapidAPI-Host": "dad-jokes.p.rapidapi.com"
        }
        async with request("GET", url, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                e = discord.Embed(color=discord.Color.blurple())
                e.title = "Here is your dad joke:"
                e.description = f"{data['body'][0]['setup']}\n\n||{data['body'][0]['punchline']}||"
                e.set_thumbnail(url="https://megaphone.imgix.net/podcasts/f9b00b92-4953-11ec-bbeb-6b1d62ae44a1/image/1619957732809-podcast_icon_v2.png?ixlib=rails-2.1.2&max-w=3000&max-h=3000&fit=crop&auto=format,compress?crop=1:1,offset-y0")
                await ctx.send(embed=e)
            else:
                await ctx.send(f"{response.status}")

    @commands.hybrid_command(aliases=['8b'], name="8ball")
    async def _8ball(self, ctx, *, question:str):
        """Ask the 8ball a question."""
        await ctx.typing()
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
            "Very doubtful."
        ]
        await ctx.send(f"Question: {question}\nAnswer: {random.choice(responses)}")

    @commands.hybrid_command()
    async def rps(self, ctx, *, choice:str):
        """Play rock paper scissors with the bot."""
        await ctx.typing()
        choices = ["rock", "paper", "scissors"]
        botChoice = random.choice(choices)
        if choice.lower() in choices:
            if choice.lower() == botChoice:
                await ctx.send(f"You both chose {choice.lower()}, it's a tie!")
            elif choice.lower() in "rock":
                if botChoice == "paper":
                    await ctx.send(f"I chose {botChoice}, you lose!")
                else:
                    await ctx.send(f"I chose {botChoice}, you win!")
            elif choice.lower() == "paper":
                if botChoice == "scissors":
                    await ctx.send(f"I chose {botChoice}, you lose!")
                else:
                    await ctx.send(f"I chose {botChoice}, you win!")
            elif choice.lower() == "scissors":
                if botChoice == "rock":
                    await ctx.send(f"I chose {botChoice}, you lose!")
                else:
                    await ctx.send(f"I chose {botChoice}, you win!")
        else:
            await ctx.send("Invalid choice, please choose rock, paper, or scissors.")

    @commands.hybrid_command()
    async def phcomment(self, ctx, *, comment: str):
        """Send a comment on PornHub. ( ͡° ͜ʖ ͡°)"""
        await ctx.typing()
        url = f"https://nekobot.xyz/api/imagegen?type=phcomment&image={ctx.author.avatar.url}&username={ctx.author.name}&text={comment}"
        async with request("GET", url) as response:
            json = await response.json();
            if json['status'] == 200:
                e = discord.Embed(color=discord.Color.blurple())
                e.set_image(url=json['message'])
                await ctx.send(embed=e)
            else:
                await ctx.send(f"{json['message']}")

    @commands.hybrid_command()
    async def ship(self, ctx, lover1: discord.Member, lover2: discord.Member=None):
        """Ship 2 users."""
        await ctx.typing()
        lover2 = lover2 or ctx.author
        rigged = False
        name1 = lover1.name[:-round(len(lover1.name) / 2)] + lover2.name[-round(len(lover2.name) / 2):]
        name2 = lover2.name[:-round(len(lover2.name) / 2)] + lover1.name[-round(len(lover1.name) / 2):]
        if 827940585201205258 in [lover1.id, lover2.id] and 882012969523884072 in [lover1.id, lover2.id]:
            rigged = True
        desc = f"**{ctx.author.mention} ships {lover1.mention} and {lover2.mention}!**\n\n " \
               f"Ship names: __**{name1}**__ or __**{name2}**__\n\n " \
               f"{self.draw_meter(rigged)}"
        e = discord.Embed(description=desc, color=discord.Color.blurple())
        return await ctx.send(embed=e)

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