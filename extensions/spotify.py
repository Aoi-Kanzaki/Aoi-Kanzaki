import time
import base64
import discord
import lavalink
from typing import List
from discord.ext import commands
from requests.auth import HTTPBasicAuth
from discord import app_commands as Aoi
from requests_oauthlib import OAuth2Session
from buttons.SpotifyCheck import Disconnect_Check
from utils.LavalinkVoiceClient import LavalinkVoiceClient


class Spotify(commands.GroupCog, description="All spotify related commands."):
    def __init__(self, bot: commands.AutoShardedBot) -> None:
        super().__init__()
        self.bot = bot
        self.db = self.bot.db.spotifyOauth

    @Aoi.command(name="info")
    async def spotify_info(self, interaction: discord.Interaction):
        """Get the info of the account that is currently connected."""
        await interaction.response.defer(ephemeral=True)
        data = await self.db.find_one({"_id": interaction.user.id})
        if data is None:
            return await interaction.followup.send(
                "You do not have an account that is connected.")
        else:
            user = await self.get_current_user(interaction)
            if user != "Failed":
                e = discord.Embed(colour=discord.Colour.teal())
                e.set_author(name=interaction.user.display_name,
                             icon_url=interaction.user.display_avatar)
                e.add_field(
                    name="Name", value=user['display_name'], inline=False)
                # e.add_field(name="Email", value=user['email'], inline=False)
                e.add_field(name="Url", value=user['uri'], inline=False)
                if user['images'] != []:
                    e.set_thumbnail(url=user['images'][0]['url'])
                return await interaction.followup.send(embed=e)
            else:
                return await interaction.followup.send(
                    "I have failed to get your account information.")

    @Aoi.command(name="connect")
    async def spotify_connect(self, interaction: discord.Interaction):
        """Connect your spotify account to Aoi."""
        await interaction.response.defer(ephemeral=True)
        data = await self.db.find_one({"_id": interaction.user.id})

        if data is not None:
            return await interaction.followup.send(
                "You already have your account linked! If you would no longer like it to be linked, you can use the command `/spotify disconnect`! <3",
                ephemeral=True)

        oauthSession = OAuth2Session(
            self.bot.config['spotify']['id'],
            scope=self.bot.config['spotify']['scope'],
            redirect_uri=self.bot.config['spotify']['redirect']
        )
        authorization_url, state = oauthSession.authorization_url(
            self.bot.config['spotify']['base_url'])
        try:
            msg = f"Please go to this link and authorize Aoi:\n{authorization_url}\n\n"
            msg += "Once authorized, please send the **entire** url of the new page it sends you to.\n\n"
            msg += "**DO NOT SEND THIS LINK OR THE NEW LINK TO ANYONE ELSE BESIDES IN AOI DMS**"
            await interaction.user.send(msg)
            await interaction.followup.send("Please check your dms to proceed!")
        except discord.errors.Forbidden:
            return await interaction.followup.edit(
                "I'm not going to able to move forward in connecting your account if you don't temporarily disable blocked dms.")

        def check(m):
            return m.author == interaction.user and m.channel == interaction.user.dm_channel

        oauthMessage = await self.bot.wait_for('message', check=check)

        auth = HTTPBasicAuth(
            self.bot.config['spotify']['id'], self.bot.config['spotify']['secret'])
        oauthData = oauthSession.fetch_token(
            self.bot.config['spotify']['token_url'],
            auth=auth,
            authorization_response=oauthMessage.content
        )
        try:
            if oauthData['access_token'] != None:
                oauthData = {"_id": interaction.user.id,
                             "oauthData": oauthData}
                await self.db.insert_one(oauthData)
                return await interaction.user.send(
                    "Your spotify account has been successfuly connected!")
        except KeyError:
            return await interaction.user.send(
                "I have failed to connect your spotify account! Please make sure you are sending the FULL link in the url bar when discord shows.")

    @Aoi.command(name="disconnect")
    async def spotify_disconnect(self, interaction: discord.Interaction):
        """This will disconnect your spotify account from Aoi and delete your data!"""
        await interaction.response.defer(ephemeral=True)
        data = await self.db.find_one({"_id": interaction.user.id})
        if data is None:
            return await interaction.followup.send(
                "You don't have a spotify account connected!",
                ephemeral=True)
        else:
            e = discord.Embed(colour=discord.Colour.teal())
            e.set_author(name=interaction.user.display_name,
                         icon_url=interaction.user.display_avatar)
            e.description = "Are you sure you want to disconnect your account?"
            return await interaction.followup.send(embed=e,
                                                   view=Disconnect_Check(self.bot, interaction), ephemeral=True)

    @Aoi.command(name="liked")
    async def spotify_liked(self, interaction: discord.Interaction):
        """Start playing all of the songs you have liked."""
        data = await self.db.find_one({"_id": interaction.user.id})
        if data is None:
            return interaction.response.send_message(
                "You do not have a spotify account connected! If you would like to connect yours please use the command `/spotify connect`! <3",
                ephemeral=True)
        else:
            liked = await self.get_liked_songs(interaction)
            if liked == "Failed":
                return await interaction.response.send_message(
                    "I failed to get your liked songs...")
            else:
                if data is None:
                    return await interaction.response.send_message("You don't have a spotify account connected!", ephemeral=True)
                liked = await self.get_liked_songs(interaction)
                if liked == "Failed":
                    return interaction.response.send_message("I have failed to get your favorite songs.")
                else:
                    try:
                        player = self.bot.lavalink.player_manager.create(
                            interaction.guild.id, endpoint="us")
                    except Exception as e:
                        self.bot.logger.error(
                            f"[Music] Failed to create player in {interaction.guild.name}: {e}")
                        self.bot.richConsole.print(
                            f"[bold red][Music][/] Failed to create player in {interaction.guild.name}: {e}")
                        if isinstance(e, lavalink.errors.NodeError):
                            return await interaction.response.send_message(
                                "<:tickNo:697759586538749982> There is no avaliable nodes right now! Try again later.", ephemeral=True)
                    if not interaction.user.voice or not interaction.user.voice.channel:
                        return await interaction.response.send_message(
                            '<:tickNo:697759586538749982> Join a voicechannel first.')
                    if not player.is_connected:
                        if (not interaction.user.voice.channel.permissions_for(interaction.guild.me).connect or not
                                interaction.user.voice.channel.permissions_for(interaction.guild.me).speak):
                            return await interaction.response.send_message(
                                '<:tickNo:697759586538749982> I need the `CONNECT` and `SPEAK` permissions.')
                        player.store('channel', interaction.channel.id)
                        await interaction.user.voice.channel.connect(cls=LavalinkVoiceClient)
                    else:
                        if int(player.channel_id) != interaction.user.voice.channel.id:
                            return await interaction.response.send_message(
                                '<:tickNo:697759586538749982> You need to be in my voicechannel.')
                    await interaction.response.send_message("<:tickYes:697759553626046546> Starting your Spotify liked songs..", ephemeral=True)
                    for track in liked['items']:
                        results = await self.bot.lavalink.get_tracks(track['track']['external_urls']['spotify'], check_local=True)
                        if results.load_type == 'PLAYLIST_LOADED':
                            tracks = results.tracks
                            for track in tracks:
                                player.add(
                                    requester=interaction.user.id, track=track)
                        else:
                            track = results.tracks[0]
                            player.add(
                                requester=interaction.user.id, track=track)
                    player.store('channel', interaction.channel.id)
                    if not player.is_playing:
                        await player.play()

    @Aoi.command(name="playlist")
    @Aoi.describe(playlist="The playlist you want to play.")
    @Aoi.checks.cooldown(1, 5)
    async def spotify_playlist(self, interaction: discord.Interaction, playlist: str = None):
        """Choose a playlist you have created, and start playing in a vc."""
        data = await self.db.find_one({"_id": interaction.user.id})
        if data is None:
            return await interaction.response.send_message(
                content="You do not have a spotify account connected! If you would like to connect yours please use the command `/spotify connect`! <3",
                ephemeral=True
            )
        else:
            if playlist != None:
                try:
                    await self.bot.get_cog('Music')._play(interaction, playlist)
                except Exception as e:
                    self.bot.logger.error(
                        f"[Spotify] Failed to play playlist in {interaction.guild.name}: {e}")
                    self.bot.richConsole.print(
                        f"[bold red][Spotify][/] Failed to play users playlist in {interaction.guild.name}: {e}")
            else:
                playlists = await self.get_playlists(interaction)
                if playlists == "Failed":
                    return await interaction.response.send_message(
                        content="I failed to get your playlists...", ephemeral=True)
                else:
                    number = 1
                    msg = ""
                    for p in playlists['items']:
                        name = p['name']
                        msg += f"`{number}.` **{name}**\n"
                        number += 1
                    e = discord.Embed(
                        colour=discord.Colour.teal(), description=msg)
                    return await interaction.response.send_message(
                        embed=e, ephemeral=True)

    @spotify_connect.error
    @spotify_disconnect.error
    @spotify_info.error
    @spotify_liked.error
    @spotify_playlist.error
    async def send_error(self, interaction: discord.Interaction, error):
        self.bot.logger.error(f"[Spotify] Error: {error}")
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

    @spotify_playlist.autocomplete('playlist')
    async def playlist_auto(self, interaction: discord.Interaction, current: str) -> List[Aoi.Choice[str]]:
        data = await self.db.find_one({"_id": interaction.user.id})
        if data != None:
            new_list = []
            playlists = await self.get_playlists(interaction)
            for playlist in playlists['items']:
                name = playlist['name']
                url = playlist['external_urls']['spotify']
                new_list.append({"name": name, "url": url})
            return [
                Aoi.Choice(name=pl['name'], value=pl['url'])
                for pl in new_list if current.lower() in str(pl['name']).lower()
            ]
        else:
            return [
                Aoi.Choice(
                    name="No account or playlists found.",
                    value="Not set up."
                )
            ]

    async def get_current_user(self, interaction: discord.Interaction):
        token = await self.get_access_token(interaction)
        if token != "Account not setup.":
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
            url = "https://api.spotify.com/v1/me/"
            async with self.bot.session.get(url, headers=headers) as session:
                try:
                    json = await session.json()
                    return json
                except:
                    return "Failed"

    async def get_playlists(self, interaction: discord.Interaction):
        token = await self.get_access_token(interaction)
        if token != "Account not setup.":
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}"
            }
            url = "https://api.spotify.com/v1/me/playlists"
            async with self.bot.session.get(url, headers=headers) as session:
                try:
                    json = await session.json()
                    if json['href'] != None:
                        return json
                except:
                    return "Failed"
        else:
            return "Account not setup."

    async def get_liked_songs(self, interaction: discord.Interaction):
        token = await self.get_access_token(interaction)
        if token != "Account not setup.":
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": "Bearer %s" % token
            }
            url = "https://api.spotify.com/v1/me/tracks"
            async with self.bot.session.get(url, headers=headers) as session:
                try:
                    json = await session.json()
                    if json['href'] != None:
                        return json
                except:
                    return "Failed"
        else:
            return "Account not setup."

    async def get_access_token(self, interaction: discord.Interaction):
        oauthData = await self.db.find_one(
            {"_id": interaction.user.id})
        if oauthData is None:
            try:
                return await interaction.followup.send(
                    "You do not have a spotify account connected!",
                    ephemeral=True)
            except:
                return "Account not setup."
        if oauthData['oauthData']['access_token'] and not oauthData['oauthData']["expires_at"] - int(time.time()) < 60:
            token = oauthData['oauthData']['access_token']
            return token
        else:
            auth_header = base64.b64encode((
                self.bot.config['spotify']['id'] + ":" +
                self.bot.config['spotify']['secret']).encode("ascii"))
            headers = {
                "Authorization": "Basic %s" % auth_header.decode("ascii"),
                "grant_type": "refresh_token",
                "refresh_token": oauthData['oauthData']['refresh_token']
            }
            data = {
                "grant_type": "refresh_token",
                "refresh_token": oauthData['oauthData']['refresh_token']
            }
            async with self.bot.session.post(self.bot.config['spotify']['token_url'],
                                             data=data, headers=headers) as session:
                json = await session.json()
                # this should be able to update the access token to the refreshed one.
                oauthData['oauthData']['access_token'] = json['access_token']
                oauthData['oauthData']['expires_at'] = int(
                    time.time()) + json["expires_in"]
                await self.db.update_one({"_id": interaction.user.id}, {
                    "$set": oauthData})
                return json['access_token']


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(Spotify(bot))
