import re
import discord
import lavalink
import aiohttp
from discord.ext import commands
from discord import app_commands as Aoi
from utils.LavalinkVoiceClient import LavalinkVoiceClient

url_rx = re.compile(r'https?:\/\/(?:www\.)?.+')


class Favorites(commands.GroupCog, description="All fav songs related commands."):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.db = self.bot.db.favorites

    @Aoi.command(name="add")
    @Aoi.describe(link="The link to the song you want to add to your favorites.")
    async def fav_add(self, interaction: discord.Interaction, link: str):
        """Adds a song to your favorites."""
        data = await self.db.find_one({"_id": interaction.user.id})
        if data is None:
            await self.db.insert_one({"_id": interaction.user.id})
            await self.db.update_one({"_id": interaction.user.id}, {
                "$set": {"songs": []}})
        else:
            if not url_rx.match(link):
                return await interaction.response.send_message(
                    "<:tickNo:697759586538749982> You need to pass a valid link to add to your favorites!")
            elif link in data['songs']:
                return await interaction.response.send_message(
                    "<:tickNo:697759586538749982> This song is already in your favorites!")
            else:
                await self.db.update_one({"_id": interaction.user.id}, {
                    "$push": {"songs": link}})
                return await interaction.response.send_message(
                    "<:tickYes:697759553626046546> Done, it's now added to your favorites!")

    @Aoi.command(name="remove")
    @Aoi.describe(link="The link of the song you want to remove from your favorites.")
    async def fav_remove(self, interaction: discord.Interaction, link: str):
        """Removes a song from your favorites."""
        data = await self.db.find_one({"_id": interaction.user.id})
        if data is None:
            return await interaction.response.send_message(
                "You don't have any favorite songs!")
        else:
            if not url_rx.match(link):
                return await interaction.response.send_message(
                    "<:tickNo:697759586538749982> You need to pass a valid link to add to your favorites!")
            elif link in data['songs']:
                await self.db.update_one({"_id": interaction.user.id}, {
                    "$pull": {"songs": link}})
                return await interaction.response.send_message(
                    "I have removed the song from your favorites!")
            else:
                return await interaction.response.send_message(
                    content="This song is not in your favorites!",
                    ephemeral=True
                )

    @Aoi.command(name="show")
    async def fav_show(self, interaction: discord.Interaction):
        """Show's how many favorite you have."""
        data = await self.db.find_one({"_id": interaction.user.id})
        if data is None:
            return await interaction.response.send_message(
                "<:tickNo:697759586538749982> You don't have any favorite songs!")
        else:
            try:
                lavalink = self.bot.lavalink
            except AttributeError:
                return await interaction.response.send_message(
                    "Music commands are currently unavaliable!", ephemeral=True)
            e = discord.Embed(colour=discord.Colour.teal())
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

    @Aoi.command(name="start")
    async def fav_start(self, interaction: discord.Interaction):
        """Start's your favorite songs."""
        data = await self.db.find_one({"_id": interaction.user.id})
        if data is None or data['songs'] == []:
            return await interaction.response.send_message("You don't have any favorite songs.", ephemeral=True)
        else:
            try:
                player = self.bot.lavalink.player_manager.create(
                    interaction.guild.id, endpoint="us")
            except Exception as error:
                self.bot.logger.error(
                    f"[Favorites] Error creating player: {error}")
                self.bot.richConsole.print(
                    f"[bold red][Favorites][/] Error while creating player: {error}")
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

    @fav_start.error
    @fav_add.error
    @fav_remove.error
    @fav_show.error
    async def send_error(self, interaction: discord.Interaction, error):
        self.bot.logger.error(f"[Favorites] Error: {error}")
        if isinstance(error, commands.MissingPermissions):
            return await interaction.response.send_message("You do not have the required permissions to use this command!", ephemeral=True)
        if isinstance(error, commands.MissingRequiredArgument):
            return await interaction.response.send_message("You are missing a required argument!", ephemeral=True)
        if isinstance(error, commands.BadArgument):
            return await interaction.response.send_message("You provided an invalid argument!", ephemeral=True)
        if isinstance(error, commands.CommandInvokeError):
            return await interaction.response.send_message("An error occurred while running this command!", ephemeral=True)
        else:
            e = discord.Embed(title="An Error has Occurred!",
                              colour=discord.Colour.red())
            e.add_field(name="Error:", value=error)
            try:
                await interaction.response.send_message(embed=e)
            except:
                await interaction.followup.send(embed=e)
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(
                    url=self.bot.config['webhooks']['mainlogs'], session=session)
                await webhook.send(embed=e)


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(Favorites(bot))
