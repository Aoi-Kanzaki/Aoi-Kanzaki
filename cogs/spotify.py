import time
import base64
import discord
from typing import List
from discord.ext import commands
from requests.auth import HTTPBasicAuth
from discord import app_commands as Fresh
from requests_oauthlib import OAuth2Session

class Disconnect_Check(discord.ui.View):
    def __init__(self, bot, interaction) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.db = self.bot.db.spotifyOauth

    @discord.ui.button(label="Yes", emoji="<:tickYes:697759553626046546>", style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.db.find_one_and_delete({"_id": interaction.user.id})
        return await interaction.response.edit_message(
            content="Your spotify account has been disconnected!", view=None, embed=None)

    @discord.ui.button(label="No", emoji="<:tickNo:697759586538749982>", style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        return await interaction.response.edit_message(
            content="Great, your account will stay connected!", view=None, embed=None)

class Spotify(commands.GroupCog, name="spotify", description="All spotify related commands."):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__()
        self.bot = bot
        self.db = self.bot.db.spotifyOauth

    @Fresh.command(name="info")
    async def spotify_info(self, interaction: discord.Interaction):
        """Get the info of the account that is currently connected."""
        await interaction.response.defer(ephemeral=True)
        data = self.db.find_one({"_id": interaction.user.id})
        if data is None:
            return await interaction.followup.send(
                "You do not have an account that is connected.")
        else:
            user = await self.get_current_user(interaction)
            if user != "Failed":
                e = discord.Embed(colour=discord.Colour.blurple())
                e.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar)
                e.add_field(name="Name", value=user['display_name'], inline=False)
                # e.add_field(name="Email", value=user['email'], inline=False)
                e.add_field(name="Url", value=user['uri'], inline=False)
                if user['images'] != []:
                    e.set_thumbnail(url=user['images'][0]['url'])
                return await interaction.followup.send(embed=e)
            else:
                return await interaction.followup.send(
                    "I have failed to get your account information.")

    @Fresh.command(name="connect")
    async def spotify_connect(self, interaction: discord.Interaction):
        """Connect your spotify account to Fresh."""
        await interaction.response.defer(ephemeral=True)
        data = self.db.find_one({"_id": interaction.user.id})

        if data is not None:
            return await interaction.followup.send(
                "You already have your account linked! If you would no longer like it to be linked, you can use the command `/spotify disconnect`! <3",
                ephemeral=True)

        oauthSession = OAuth2Session(
            self.bot.config['spotify']['id'],
            scope=self.bot.config['spotify']['scope'],
            redirect_uri=self.bot.config['spotify']['redirect']
        )
        authorization_url, state = oauthSession.authorization_url(self.bot.config['spotify']['base_url'])
        try:
            msg = f"Please go to this link and authorize Fresh:\n{authorization_url}\n\n"
            msg += "Once authorized, please send the **entire** url of the new page it sends you to.\n\n"
            msg += "**DO NOT SEND THIS LINK OR THE NEW LINK TO ANYONE ELSE BESIDES IN FRESH DMS**"
            await interaction.user.send(msg)
            await interaction.followup.send("Please check your dms to proceed!")
        except discord.errors.Forbidden:
            return await interaction.followup.edit(
                "I'm not going to able to move forward in connecting your account if you don't temporarily disable blocked dms.")

        def check(m):
            return m.author == interaction.user and m.channel == interaction.user.dm_channel

        oauthMessage = await self.bot.wait_for('message', check=check)

        auth = HTTPBasicAuth(self.bot.config['spotify']['id'], self.bot.config['spotify']['secret'])
        oauthData = oauthSession.fetch_token(
            self.bot.config['spotify']['token_url'],
            auth=auth,
            authorization_response=oauthMessage.content
        )
        try:
            if oauthData['access_token'] != None:
                oauthData = {"_id": interaction.user.id, "oauthData": oauthData}
                self.db.insert_one(oauthData)
                return await interaction.user.send(
                    "Your spotify account has been successfuly connected!")
        except KeyError:
            return await interaction.user.send(
                "I have failed to connect your spotify account! Please make sure you are sending the FULL link in the url bar when discord shows.")
        

    @Fresh.command(name="disconnect")
    async def spotify_disconnect(self, interaction: discord.Interaction):
        """This will disconnect your spotify account from Fresh and delete your data!"""
        await interaction.response.defer(ephemeral=True)
        data = self.db.find_one({"_id": interaction.user.id})
        if data is None:
            return await interaction.followup.send(
                "You don't have a spotify account connected!",
                ephemeral=True)
        else:
            e = discord.Embed(colour=discord.Colour.blurple())
            e.set_author(name=interaction.user.display_name, icon_url=interaction.user.display_avatar)
            e.description = "Are you sure you want to disconnect your account?"
            return await interaction.followup.send(embed=e,
                    view=Disconnect_Check(self.bot, interaction), ephemeral=True)


    @Fresh.command(name="liked")
    async def spotify_liked(self, interaction: discord.Interaction):
        """Start playing all of the songs you have liked."""
        data = self.db.find_one({"_id": interaction.user.id})
        if data is None:
            return interaction.response.send_message(
                "You do not have a spotify account connected! If you would like to connect yours please use the command `/spotify connect`! <3",
                ephemeral=True)
        else:
            liked = "not done" #await self.get_liked_songs(interaction)
            if liked == "Failed":
                return await interaction.response.send_message(
                        "I failed to get your liked songs...")
            else:
                return await interaction.response.send_message("Not done implementing. <3")


    @commands.cooldown(1, 5, commands.BucketType.user)
    @Fresh.command(name="playlist")
    async def spotify_playlist(self, interaction: discord.Interaction, playlist: str=None):
        """Choose a playlist you have created, and start playing in a vc."""
        await interaction.response.defer(ephemeral=True)
        data = self.db.find_one({"_id": interaction.user.id})
        if data is None:
            return await interaction.followup.send(
                "You do not have a spotify account connected! If you would like to connect yours please use the command `/spotify connect`! <3")
        else:
            if playlist != None:
                await self.bot.get_cog('Music')._play(interaction, playlist)
                # return await interaction.followup.send(
                #         f"Here is when I need to play this playlist right?\n{playlist}")
            else:
                playlists = await self.get_playlists(interaction)
                if playlists == "Failed":
                    return await interaction.followup.send(
                        "I failed to get your playlists...")
                else:
                    number = 1
                    msg = ""
                    # results = []
                    for p in playlists['items']:
                        name = p['name']
                        # description = p['description']
                        # uri = p['external_urls']['spotify']
                        # image = p['images'][0]['url']
                        # numTracks = p['tracks']['total']
                        # results.append({"name": name, "desc": description, "uri": uri, "image": image, "numTracks": numTracks})
                        msg += f"`{number}.` **{name}**\n"
                        number += 1
                    e = discord.Embed(colour=discord.Colour.blurple(), description=msg)
                    return await interaction.followup.send(embed=e)


    @spotify_playlist.autocomplete('playlist')
    async def playlist_auto(self, interaction: discord.Interaction, current: str) -> List[Fresh.Choice[str]]:
        data = self.db.find_one({"_id": interaction.user.id})
        if data != None:
            new_list = []
            playlists = await self.get_playlists(interaction)
            for playlist in playlists['items']:
                name = playlist['name']
                url = playlist['external_urls']['spotify']
                new_list.append({"name": name, "url": url})
            return [
                Fresh.Choice(name=pl['name'], value=pl['url'])
                for pl in new_list if current.lower() in str(pl['name']).lower()
            ]
        else:
            return [
                Fresh.Choice(
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
        oauthData = self.db.find_one({"_id": interaction.user.id})
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
                oauthData['oauthData']['expires_at'] = int(time.time()) + json["expires_in"]
                self.db.update_one({"_id": interaction.user.id}, {"$set": oauthData})
                return json['access_token']


async def setup(bot):
    await bot.add_cog(Spotify(bot))