import discord
import json
import urllib
from aiohttp import request
from discord.ext import commands

class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def meme(self, ctx):
        """You want memes???"""
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

    @commands.command(aliases=['dj'])
    async def dadjoke(self, ctx):
        """Get a random dad joke."""
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

    @commands.command(aliases=['8b'], name="8ball")
    async def _8ball(self, ctx, *, question:str):
        """Find the answers to your questions. It knows, and is willing to share."""
        url = "https://magic-8-ball1.p.rapidapi.com/my_answer/"
        querystring = {"question": question}
        headers = {
	        "X-RapidAPI-Key": "ef73cad338msh002fd3975548b99p1f8db4jsna8c2f9e965d1",
	        "X-RapidAPI-Host": "magic-8-ball1.p.rapidapi.com"
        }
        async with request("GET", url, headers=headers, params=querystring) as response:
            if response.status == 200:
                data = await response.json()
                await ctx.reply(f"{ctx.author.mention} {data['answer']}")
            else:
                await ctx.send(f"{response.status}")

async def setup(bot):
    await bot.add_cog(Fun(bot))