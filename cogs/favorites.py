import re
import discord
from discord.ext import commands

url_rx = re.compile(r'https?:\/\/(?:www\.)?.+')

class Favorites(commands.Cog):
    def __init__(self, bot):
        fresh = bot.tree
        self.bot = bot
        self.db = self.bot.db.favorites

        @fresh.command(name="favadd")
        async def fav_add(interaction: discord.Interaction, link: str):
            """Adds a song to your favorites."""
            data = self.db.find_one({"_id": interaction.user.id})
            if data is None:
                self.db.insert_one({"_id": interaction.user.id})
                self.db.update_one({"_id": interaction.user.id}, {"$set": {"songs": []}})
            else:
                if not url_rx.match(link):
                    return await interaction.response.send_message(
                        "<:tickNo:697759586538749982> You need to pass a valid link to add to your favorites!")
                else:
                    self.db.update_one({"_id": interaction.user.id}, {"$push": {"songs": link}})
                    return await interaction.response.send_message(
                        "<:tickYes:697759553626046546> Done, it's now added to your favorites!")

        @fresh.command(name="favshow")
        async def fav_show(interaction: discord.Interaction):
            """Show's how many favorite you have."""
            data = self.db.find_one({"_id": interaction.user.id})
            if data is None:
                return await interaction.response.send_message(
                    "<:tickNo:697759586538749982> You don't have any favorite songs!")
            else:
                e = discord.Embed(colour=discord.Color.blurple())
                e.set_author(
                    icon_url=interaction.user.display_avatar.url,
                    name=f"{interaction.user.display_name}'s Favorite Songs:"
                )
                e.description = ""
                number = 1
                for song in data['songs'][0:5]:
                    if not url_rx.match(song):
                        song = f'spsearch:{song}'
                    result = await self.bot.lavalink.get_tracks(song, check_local=True)
                    e.description += f"`{number}.` {result['tracks'][0]['title']}\n"
                    number += 1
                if len(data['songs']) > 5:
                    total = len(data['songs']) - 5
                    e.description += f"\nNot showing **{total}** more songs..."
                return await interaction.response.send_message(embed=e)

        @fresh.context_menu(name="Favorite Songs")
        async def fav_songs_context(interaction: discord.Interaction, member: discord.Member):
            """Show's a users favorite songs."""
            data = self.db.find_one({"_id": member.id})
            if data is None:
                return await interaction.response.send_message(
                    f"<:tickNo:697759586538749982> **{member.display_name}** doesn't have any favorite songs!")
            else:
                e = discord.Embed(colour=discord.Color.blurple())
                e.set_author(
                    icon_url=member.display_avatar,
                    name=f"{member.display_name}'s Favorite Songs:"
                )
                e.description = ""
                number = 1
                for song in data['songs'][0:5]:
                    if not url_rx.match(song):
                        song = f'spsearch:{song}'
                    result = await self.bot.lavalink.get_tracks(song, check_local=True)
                    e.description += f"`{number}.` {result['tracks'][0]['title']}\n"
                    number += 1
                if len(data['songs']) > 5:
                    total = len(data['songs']) - 5
                    e.description += f"\nNot showing **{total}** more songs..."
                return await interaction.response.send_message(embed=e)

async def setup(bot):
    await bot.add_cog(Favorites(bot))
