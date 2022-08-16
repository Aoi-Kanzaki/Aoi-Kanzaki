import discord
from discord.ext import commands
from requests import delete


class Playlists(commands.Cog):
    """Create user playlists."""

    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_group()
    async def playlists(self, ctx):
        """Shows you commands for your playlists."""
        if ctx.invoked_subcommand is None:
            await self.bot.send_sub_help(ctx, ctx.command)

    @playlists.command()
    async def show(self, ctx, *, playlist: str = None):
        """Shows your saved playlists."""
        settings = {"_id": ctx.author.id}
        data = await self.bot.db.playlists.find_one({"_id": ctx.author.id})
        if not data or data == settings:
            return await ctx.send("<:tickNo:697759586538749982> You don't have any playlists.")
        keys = {k: v for k, v in data.items() if not k.endswith("_id")}
        e = discord.Embed(color=discord.Colour.blurple())
        e.set_thumbnail(url=ctx.author.avatar)
        if playlist is None:
            number = 0
            e.set_author(name="Here are your playlists:", icon_url=ctx.author.avatar)
            e.description = f"For more info on a playlist try {ctx.prefix}playlists show  <playlist>\n\n**Available Playlists:**\n"
            for key, val in data.items():
                if "_id" in key:
                    continue
                number += 1
                e.description += f"`{number})` {key}\n"
            if e.description == "":
                return await ctx.send("<:tickNo:697759586538749982> You don't have any playlists.", delete_after=5)
        if playlist is not None:
            number = 0
            for link in data[playlist]:
                number += 1
            if playlist not in keys:
                return await ctx.send("<:tickNo:697759586538749982> Playlist not found with that name.", delete_after=5)
            e.set_author(name=f"More info on playlist {playlist}:", icon_url=ctx.author.avatar)
            e.add_field(name="Playlist:", value=playlist)
            e.add_field(name="# of links:", value=len(data[playlist]))
            if number == 0:
                e.add_field(name="Playlist Links:", value="This playlist is empty.", inline=False)
            if number > 0:
                if len(data[playlist]) < 10:
                    e.add_field(name="Playlist links:", value="\n".join(link for link in data[playlist]), inline=False)
                elif len(data[playlist]) == 10:
                    e.add_field(name="Playlist links:", value=f"I cannot show all the links.", inline=False)
                elif len(data[playlist]) > 10:
                    e.add_field(name="Playlist links:", value=f"I can only show the first 10 links.", inline=False)
        return await ctx.send(embed=e)

    @playlists.command(name="add")
    async def add(self, ctx, name: str, *, link: str = None):
        """Add a playlists to you database."""
        data = await self.bot.db.playlists.find_one({"_id": ctx.author.id})
        if name is None:
            return await ctx.send("<:tickNo:697759586538749982> Playlist name cannot be empty.", delete_after=5)
        if not data:
            await self.bot.db.playlists.insert_one({"_id": ctx.author.id})
        await self.bot.db.playlists.update_one({"_id": ctx.author.id}, {"$set": {name: []}})
        if link is not None:
            await self.bot.db.playlists.update_one({"_id": ctx.author.id}, {"$push": {name: link}})
        return await ctx.send("<:tickYes:697759553626046546> Done!", delete_after=5)

async def setup(bot):
    await bot.add_cog(Playlists(bot))
