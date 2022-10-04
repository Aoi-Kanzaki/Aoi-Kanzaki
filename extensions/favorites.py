import re
import discord
import lavalink
from discord.ext import commands
from discord import app_commands as Fresh
from utils.LavalinkVoiceClient import LavalinkVoiceClient

url_rx = re.compile(r'https?:\/\/(?:www\.)?.+')


class Favorites(commands.GroupCog, name="favorites", description="All fav songs related commands."):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db.favorites

        @Fresh.context_menu(name="Favorite Songs")
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
                    try:
                        result = await self.bot.lavalink.get_tracks(song, check_local=True)
                    except:
                        return await interaction.response.send_message(
                            "The music module is not enabled! Or I have encountered a more serious error.", ephemeral=True)
                    e.description += f"`{number}.` {result['tracks'][0]['title']}\n"
                    number += 1
                if len(data['songs']) > 5:
                    total = len(data['songs']) - 5
                    e.description += f"\nNot showing **{total}** more songs..."
                return await interaction.response.send_message(embed=e)

    @Fresh.command(name="add")
    async def fav_add(self, interaction: discord.Interaction, link: str):
        """Adds a song to your favorites."""
        data = self.db.find_one({"_id": interaction.user.id})
        if data is None:
            self.db.insert_one({"_id": interaction.user.id})
            self.db.update_one({"_id": interaction.user.id}, {
                               "$set": {"songs": []}})
        else:
            if not url_rx.match(link):
                return await interaction.response.send_message(
                    "<:tickNo:697759586538749982> You need to pass a valid link to add to your favorites!")
            elif link in data['songs']:
                return await interaction.response.send_message(
                    "<:tickNo:697759586538749982> This song is already in your favorites!")
            else:
                self.db.update_one({"_id": interaction.user.id}, {
                                   "$push": {"songs": link}})
                return await interaction.response.send_message(
                    "<:tickYes:697759553626046546> Done, it's now added to your favorites!")

    @Fresh.command(name="remove")
    async def fav_remove(self, interaction: discord.Interaction, link: str):
        """Removes a song from your favorites."""
        data = self.db.find_one({"_id": interaction.user.id})
        if data is None:
            return await interaction.response.send_message(
                "You don't have any favorite songs!")
        else:
            if not url_rx.match(link):
                return await interaction.response.send_message(
                    "<:tickNo:697759586538749982> You need to pass a valid link to add to your favorites!")
            elif link in data['songs']:
                self.db.update_one({"_id": interaction.user.id}, {
                                   "$pull": {"songs": link}})
                return await interaction.response.send_message(
                    "I have removed the song from your favorites!")
            else:
                return await interaction.response.send_message(
                    content="This song is not in your favorites!",
                    ephemeral=True
                )

    @Fresh.command(name="show")
    async def fav_show(self, interaction: discord.Interaction):
        """Show's how many favorite you have."""
        data = self.db.find_one({"_id": interaction.user.id})
        if data is None:
            return await interaction.response.send_message(
                "<:tickNo:697759586538749982> You don't have any favorite songs!")
        else:
            try:
                lavalink = self.bot.lavalink
            except AttributeError:
                return await interaction.response.send_message(
                    "Music commands are currently unavaliable!", ephemeral=True)
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
                result = await lavalink.get_tracks(song, check_local=True)
                e.description += f"`{number}.` {result['tracks'][0]['title']}\n"
                number += 1
            if len(data['songs']) > 5:
                total = len(data['songs']) - 5
                e.description += f"\nNot showing **{total}** more songs..."
            return await interaction.response.send_message(embed=e)

    @Fresh.command(name="start")
    async def start(self, interaction: discord.Interaction):
        """Start's your favorite songs."""
        data = self.db.find_one({"_id": interaction.user.id})
        if data is None or data['songs'] == []:
            return await interaction.response.send_message("You don't have any favorite songs.", ephemeral=True)
        else:
            try:
                player = self.bot.lavalink.player_manager.create(
                    interaction.guild.id, endpoint="us")
            except Exception as error:
                print(error)
                if isinstance(error, lavalink.errors.NodeError):
                    return await interaction.response.send_message(
                        "<:tickNo:697759586538749982> There is no avaliable nodes right now! Try again later.", ephemeral=True)
            if not interaction.user.voice or not interaction.user.voice.channel:
                return await interaction.response.send_message(
                    '<:tickNo:697759586538749982> Join a voicechannel first.', ephemeral=True)
            if not player.is_connected:
                if (not interaction.user.voice.channel.permissions_for(interaction.guild.me).connect or not
                        interaction.user.voice.channel.permissions_for(interaction.guild.me).speak):
                    return await interaction.response.send_message(
                        '<:tickNo:697759586538749982> I need the `CONNECT` and `SPEAK` permissions.', ephemeral=True)
                player.store('channel', interaction.channel.id)
                await interaction.user.voice.channel.connect(cls=LavalinkVoiceClient)
            else:
                if int(player.channel_id) != interaction.user.voice.channel.id:
                    return await interaction.response.send_message(
                        '<:tickNo:697759586538749982> You need to be in my voicechannel.', ephemeral=True)
            await interaction.response.send_message("<:tickYes:697759553626046546> I am now starting your favorite songs!", ephemeral=True)
            for song in data['songs']:
                results = await self.bot.lavalink.get_tracks(song, check_local=True)
                if results.load_type == 'PLAYLIST_LOADED':
                    tracks = results.tracks
                    for track in tracks:
                        player.add(requester=interaction.user.id, track=track)
                else:
                    track = results.tracks[0]
                    player.add(requester=interaction.user.id, track=track)
            player.store('channel', interaction.channel.id)
            if not player.is_playing:
                await player.play()


async def setup(bot):
    await bot.add_cog(Favorites(bot))
