import json
import discord
import aiosqlite
import requests
import datetime
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

    @commands.command(aliases=["setp"])
    @commands.has_permissions(manage_guild=True)
    async def setprefix(self, ctx, prefix=None):
        """Set the bots prefix fot this guild."""
        if prefix is None:
            prefix = "f?"
        with open('./data/prefixes.json', 'r') as f:
            prefixes = json.load(f)
        prefixes[str(ctx.guild.id)] = prefix
        with open('./data/prefixes.json', 'w') as f:
            json.dump(prefixes, f, indent=4)
        await ctx.send(f"The bot's prefix has been changed to `{prefix}`.")

async def setup(bot):
    await bot.add_cog(Utility(bot))