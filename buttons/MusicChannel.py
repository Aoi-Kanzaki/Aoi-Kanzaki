import discord
import lavalink
import datetime
import humanize
from aiohttp import request
from sources.spotify import SpotifyAudioTrack
from buttons.EnsureChoice import EnsureChoiceButtons
from utils.LavalinkVoiceClient import LavalinkVoiceClient


class DefaultButtons(discord.ui.View):
    def __init__(self, bot) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.db = self.bot.db.spotifyOauth

    @discord.ui.button(label="Start My Favorites", custom_id="start_fav", style=discord.ButtonStyle.green)
    async def start_fav(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.bot.db.favorites.find_one({"_id": interaction.user.id})
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

    @discord.ui.button(label="Start Spotify Liked", custom_id="spotify_liked", style=discord.ButtonStyle.green)
    async def spotify_liked(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.db.find_one({"_id": interaction.user.id})
        if data is None:
            return await interaction.response.send_message("You don't have a spotify account connected!", ephemeral=True)
        liked = await self.bot.get_cog('Spotify').get_liked_songs(interaction)
        if liked == "Failed":
            return interaction.response.send_message("I have failed to get your favorite songs.")
        else:
            try:
                player = self.bot.lavalink.player_manager.create(
                    interaction.guild.id, endpoint="us")
            except Exception as e:
                print(e)
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
            await interaction.response.send_message("<a:loading:697759686509985814> Starting your Spotify liked songs..", ephemeral=True)
            for track in liked['items']:
                results = await self.bot.lavalink.get_tracks(track['track']['external_urls']['spotify'], check_local=True)
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


class PlayingButtons(discord.ui.View):
    def __init__(self, bot, guild_id) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.fav = self.bot.db.favorites
        self.db = self.bot.db.musicChannel
        self.data = self.db.find_one({"_id": guild_id})
        self.player = bot.lavalink.player_manager.get(guild_id)

    @discord.ui.button(emoji="🤍", style=discord.ButtonStyle.grey)
    async def love_song(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.fav.find_one({"_id": interaction.user.id})
        if data is None:
            self.fav.insert_one({"_id": interaction.user.id})
            self.fav.update_one({"_id": interaction.user.id}, {
                                "$set": {"songs": [self.player.current.uri]}})
            return await interaction.response.send_message(
                "<:tickYes:697759553626046546> Done, it's now added to your favorites!", ephemeral=True)
        else:
            if self.player.current.uri in data['songs']:
                e = discord.Embed(colour=discord.Colour.red())
                e.set_author(
                    name=interaction.user.display_name, icon_url=interaction.user.display_avatar)
                e.description = "This song seems to already be in your favorite songs?\n"
                e.description += "Would you like to remove it?"
                await interaction.response.send_message(
                    embed=e, view=EnsureChoiceButtons(self.bot, self.player.current.uri), ephemeral=True)
            else:
                self.fav.update_one({"_id": interaction.user.id}, {
                                    "$push": {"songs": self.player.current.uri}})
                return await interaction.response.send_message(
                    "<:tickYes:697759553626046546> Done, it's now added to your favorites!", ephemeral=True)

    @discord.ui.button(emoji="<:pause:1010305240672780348>", style=discord.ButtonStyle.gray)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_pause(not self.player.paused)
        if self.player.paused:
            title = "Paused:"
            button.emoji = "<:play:1010305312227606610>"
        else:
            button.emoji = "<:pause:1010305240672780348>"
            title = "Currently Playing:"
        e = discord.Embed(colour=discord.Colour.teal(), title=title)
        if self.player.current.stream:
            duration = '🔴 LIVE'
        else:
            dur = self.player.current.duration
            delta = datetime.timedelta(milliseconds=dur)
            duration = humanize.naturaldelta(delta)
        fmt = f'{self.player.current.title} - {self.player.current.author}'
        e.description = f'**{fmt}**\n*[Link to Song]({self.player.current.uri})*'
        e.add_field(name="Duration:", value=duration)
        e.add_field(name="Requested By:",
                    value=f"<@!{self.player.current.requester}>")
        if self.player.queue:
            queueList = ''
            for index, track in enumerate(self.player.queue[0:5], start=0):
                queueList += f'`{index+1}.` [{track.title}]({track.uri})\n'
            e.add_field(name="Queue List:", value=queueList, inline=False)
        else:
            e.add_field(
                name="Queue List:", value="Join a voice channel and queue songs by name or url in here.",
                inline=False)
        if "open.spotify.com" in str(self.player.current.uri):
            url = f"https://open.spotify.com/oembed?url={self.player.current.uri}"
            async with request("GET", url) as response:
                json = await response.json()
                e.set_image(url=f"{json['thumbnail_url']}")
        else:
            e.set_image(
                url=f"https://img.youtube.com/vi/{self.player.current.identifier}/hqdefault.jpg")
        return await interaction.response.edit_message(embed=e, view=self)

    @discord.ui.button(emoji="<:skip:1010321396301299742>", style=discord.ButtonStyle.grey)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.player.is_playing:
            await self.player.skip()
            return await interaction.response.send_message(
                content="Skipped.",
                ephemeral=True
            )
        else:
            return await interaction.response.send_message(
                content="Nothing playing.",
                ephemeral=True
            )

    @discord.ui.button(emoji="<:shuffle:1033963011657977876>", style=discord.ButtonStyle.grey)
    async def shuffle(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.player.shuffle = not self.player.shuffle
        return await interaction.response.send_message(
            content='🔀 | Shuffle ' +
            ('enabled' if self.player.shuffle else 'disabled'),
            ephemeral=True
        )

    @discord.ui.button(emoji="<:stop:1010325505179918468>", style=discord.ButtonStyle.red)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(content="⏹️ Stopping music and clearing the queue...", ephemeral=True)
        if self.data != None and interaction.channel.id == self.data['channel']:
            channel = await self.bot.fetch_channel(self.data['channel'])
            msg = await channel.fetch_message(self.data['message'])
            e = discord.Embed(
                colour=discord.Colour.teal(),
                description="Send a song link or query to start playing music!\nOr click the button to start you favorite songs!",
            )
            e.set_author(
                name=f"{self.bot.user.name} Music:",
                icon_url=self.bot.user.avatar
            )
            e.set_image(url=self.bot.user.avatar)
            await msg.edit(embed=e, view=DefaultButtons(self.bot))
        self.player.queue.clear()
        await self.player.stop()
        await interaction.guild.voice_client.disconnect(force=True)
