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
    async def add(self, ctx, name: str, *, song: str=None):
        """Add a playlists to your database."""
        data = await self.bot.db.playlists.find_one({"_id": ctx.author.id})
        if name is None:
            return await ctx.send("<:tickNo:697759586538749982> Playlist name cannot be empty.", delete_after=5)
        if not data:
            await self.bot.db.playlists.insert_one({"_id": ctx.author.id})
        await self.bot.db.playlists.update_one({"_id": ctx.author.id}, {"$set": {name: []}})
        if song is not None:
            await self.bot.db.playlists.update_one({"_id": ctx.author.id}, {"$push": {name: song}})
        return await ctx.send("<:tickYes:697759553626046546> Done!", delete_after=5)

    @playlists.command("del")
    async def delete(self, ctx, name: str=None):
        """Deletes a playlist from your database."""
        data = await self.bot.db.playlists.find_one({"_id": ctx.author.id})
        if not data:
            return await ctx.send("<:tickNo:697759586538749982> You don't have any playlists.")
        else:
            keys = {k:v for k,v in data.items() if not k.endswith('_id')}
            if name not in keys:
                return await ctx.send("<:tickNo:697759586538749982> Playlist not found.")
            await self.bot.db.playlists.update_one({"user_id": ctx.author.id}, {"$unset":{name: keys[name]}})
            await ctx.send("<:tickYes:697759553626046546> Deleted.", delete_after=5)


    @playlists.command(aliases=['tut', 'howto'])
    async def tutorial(self, ctx):
        await ctx.typing()
        msg = f"Hi there {ctx.author.mention}, it seem's you're a bit lost on how this works.\n"
        msg += "Don't worry, because that's what this command is for, to show you how to use the playlists feature.\n"
        msg += "First things first, you will need to create a playlist. But before I tell you how, I want to go over the fundamentals.\n\n"
        msg += "When creating a playlist you will have two options on how to pass a song.\n"
        msg += "    `1.` You can use the song name like `logic nikki`\n    `2.` Or you can use a spotify or youtube link.\n\n"
        msg += "Now that you know how to pass a song, we can now move onto creating your first playlist.\n"
        msg += f"To create a playlist use the command `{ctx.prefix}playlists add`.\n"
        msg += "    **Examples:**\n"
        msg += f"      `1.` {ctx.prefix}playlists add PlaylistName logic nikki\n"
        msg += f"      `2.` {ctx.prefix}playlist add PlaylistName spotifylink\n"
        msg += f"      `3.` {ctx.prefix}playlist add PlaylistName youtubelink\n\n"
        msg += "Perfect! You've created your first playlist! Now let's move on. You now have more options that you can do.\n"
        msg += f"   `1.` You can view your avaliable playlists using the command {ctx.prefix}playlists show\n"
        msg += f"   `2.` You can view one of your playlist using the command {ctx.prefix}playlists show PlaylistName\n"
        msg += f"   `3.` You can now join a voice channel and start a playlist using the command {ctx.prefix}playlist start PlaylistName\n\n"
        msg += "I hope this helped! Now go create a playlist and try it out for yourself! If you need any further assistance you can join the support server in my bio."
        await ctx.send(msg)


async def setup(bot):
    await bot.add_cog(Playlists(bot))
