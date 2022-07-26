import re
import math
import discord
import lavalink
import aiohttp
import humanize
import datetime
import asyncio
from aiohttp import request
from discord.ext import commands
from lavalink.filters import LowPass
from discord import app_commands as Aoi

from sources.spotify import SpotifyAudioTrack, SpotifySource
from utils.LavalinkVoiceClient import LavalinkVoiceClient
from buttons.QueueMessage import QueueButtons
from buttons.TrackStartEvent import TrackStartEventButtons
from buttons.MusicChannel import DefaultButtons, PlayingButtons
from buttons.NowPlaying import NowPlaying

url_rx = re.compile(r'https?://(?:www\.)?.+')


class Music(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        if not hasattr(bot, 'lavalink'):
            bot.lavalink = lavalink.Client(bot.user.id)
            # Host, Port, Password, Region, Name
            bot.lavalink.add_node(
                self.bot.config['lavalink']['host'],
                self.bot.config['lavalink']['port'],
                self.bot.config['lavalink']['pass'],
                self.bot.config['lavalink']['region'],
                self.bot.config['lavalink']['name']
            )

        bot.lavalink.add_event_hooks(self)
        self.reload_sources()

    async def query_auto(self, interaction: discord.Interaction, current: str):
        await asyncio.sleep(0.3)
        if url_rx.match(current):
            return [Aoi.Choice(name=current, value=current)]
        elif current.startswith(('artist:')):
            return [Aoi.Choice(name=current, value=current)]
        else:
            current = f'spsearch:{current}'
            try:
                results = await self.bot.lavalink.get_tracks(current, check_local=True)
            except lavalink.errors.LoadError:
                return [Aoi.Choice(name="Nothing found..", value="Nothing found..")]
            if not results.tracks:
                return [Aoi.Choice(name="Nothing found..", value="Nothing found..")]
            else:
                return [
                    Aoi.Choice(
                        name=f"{track.author} - {track.title}", value=track.uri)
                    for track in results.tracks
                ][0:5]

    @Aoi.command(name="play")
    @Aoi.describe(query="The song you want to play.")
    @Aoi.autocomplete(query=query_auto)
    async def play(self, interaction: discord.Interaction, query: str):
        """ Searches and plays a song from a given query. """
        await self._play(interaction, query)

    async def _play(self, interaction: discord.Interaction, query: str):
        inVoice = await self.ensure_voice(interaction)
        if inVoice:
            try:
                player = self.bot.lavalink.player_manager.players.get(
                    interaction.guild.id)
                query = query.strip('<>')
                e = discord.Embed(color=discord.Colour.teal())
                if not url_rx.match(query) and not query.startswith(('artist:')):
                    query = f'spsearch:{query}'
                results = await self.bot.lavalink.get_tracks(query, check_local=True)
                if not results or not results.tracks:
                    try:
                        return await interaction.response.send_message('Nothing found.')
                    except:
                        return await interaction.followup.send('Nothing found.')
                if results.load_type == 'PLAYLIST_LOADED':
                    tracks = results.tracks
                    for track in tracks:
                        player.add(requester=interaction.user.id, track=track)
                    e.title = "Playlist Enqueued!"
                    e.description = f"{results.playlist_info.name} with {len(tracks)} tracks."
                    try:
                        await interaction.response.send_message(embed=e, ephemeral=True)
                    except:
                        await interaction.followup.send(embed=e)
                else:
                    track = results.tracks[0]
                    player.add(requester=interaction.user.id, track=track)
                    if player.queue:
                        e.title = "Track Enqueued!"
                        e.description = f"{track.title}\n{track.uri}"
                        try:
                            await interaction.response.send_message(embed=e, ephemeral=True)
                        except:
                            await interaction.followup.send(embed=e)
                player.store('channel', interaction.channel.id)
                if not player.is_playing:
                    await player.play()
            except lavalink.errors.LoadError:
                try:
                    return await interaction.response.send_message('Spotify API did not return a valid response!')
                except:
                    return await interaction.followup.send('Spotify API did not return a valid response!')

    @Aoi.command(name="liked")
    async def liked(self, interaction: discord.Interaction):
        """Start's all the songs you have favorited."""
        data = await self.bot.db.favorites.find_one({"_id": interaction.user.id})
        if data is None or data['songs'] == []:
            return await interaction.response.send_message("You don't have any favorite songs.", ephemeral=True)
        else:
            try:
                player = self.bot.lavalink.player_manager.create(
                    interaction.guild.id, endpoint="us")
            except Exception as error:
                self.bot.logger.error(
                    f"[Music] Error creating player: {error}")
                self.bot.richConsole.print(
                    f"[bold red][Music][/] Error while creating player: {error}")
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

    @Aoi.command(name="seek")
    @Aoi.describe(seconds="The amount of seconds you want to seek.")
    async def seek(self, interaction: discord.Interaction, seconds: int):
        """Seeks to a given position in a track."""
        inVoice = await self.ensure_voice(interaction)
        if inVoice:
            player = self.bot.lavalink.player_manager.players.get(
                interaction.guild.id)
            if player.is_playing:
                track_time = max(0, player.position + (seconds * 1000))
                await player.seek(track_time)
                return await interaction.response.send_message(
                    content=f'Moved track to **{lavalink.utils.format_time(track_time)}**',
                    ephemeral=True
                )
            else:
                return await interaction.response.send_message(
                    content="Nothing playing.",
                    ephemeral=True
                )

    @Aoi.command(name="skip")
    async def skip(self, interaction: discord.Interaction):
        """Skips the current song."""
        inVoice = await self.ensure_voice(interaction)
        if inVoice:
            player = self.bot.lavalink.player_manager.players.get(
                interaction.guild.id)
            if player.is_playing:
                await player.skip()
                return await interaction.response.send_message(
                    content="Skipped.",
                    ephemeral=True
                )
            else:
                return await interaction.response.send_message(
                    content="Nothing playing.",
                    ephemeral=True
                )

    @Aoi.command(name="stop")
    async def stop(self, interaction: discord.Interaction):
        """Stops the current queue and clears it."""
        inVoice = await self.ensure_voice(interaction)
        if inVoice:
            player = self.bot.lavalink.player_manager.players.get(
                interaction.guild.id)
            if player.is_playing:
                player.queue.clear()
                await player.stop()
                return await interaction.response.send_message(
                    content="Stopped the player and cleared the queue.",
                    ephemeral=True
                )
            else:
                return await interaction.response.send_message(
                    content="Nothing playing.",
                    ephemeral=True
                )

    @Aoi.command(name="now")
    async def now(self, interaction: discord.Interaction):
        """Shows the current song that is playing."""
        inVoice = await self.ensure_voice(interaction)
        if inVoice:
            player = self.bot.lavalink.player_manager.players.get(
                interaction.guild.id)
            if player.is_playing:
                position = lavalink.utils.format_time(player.position)
                if player.current.stream:
                    duration = '🔴 LIVE'
                else:
                    dur = player.current.duration
                    delta = datetime.timedelta(milliseconds=dur)
                    duration = humanize.naturaldelta(delta)
                fmt = f'{player.current.title} - {player.current.author}' \
                    if isinstance(player.current, SpotifyAudioTrack) else player.current.title
                song = f'**[{fmt}]({player.current.uri})**\n({position}/{duration})'
                embed = discord.Embed(
                    color=discord.Colour.teal(), title='Now Playing', description=song)
                if "open.spotify.com" in str(player.current.uri):
                    url = f"https://open.spotify.com/oembed?url={player.current.uri}"
                    async with request("GET", url) as response:
                        json = await response.json()
                        embed.set_thumbnail(url=f"{json['thumbnail_url']}")
                else:
                    embed.set_thumbnail(
                        url=f"https://img.youtube.com/vi/{player.current.identifier}/hqdefault.jpg")
                    song = f'**[{fmt}]({player.current.uri})**\n({position}/{duration})'
                return await interaction.response.send_message(
                    embed=embed,
                    ephemeral=True,
                    view=NowPlaying(self.bot, player.guild_id)
                )
            else:
                return await interaction.response.send_message(
                    content="Nothing playing.",
                    ephemeral=True
                )

    @Aoi.command(name="queue")
    @Aoi.describe(page="The page you want to see.")
    async def queue(self, interaction: discord.Interaction, page: int = 1):
        """Shows the current queue."""
        inVoice = await self.ensure_voice(interaction)
        if inVoice:
            player = self.bot.lavalink.player_manager.get(
                interaction.guild.id)
            if player.queue:
                itemsPerPage = 10
                pages = math.ceil(len(player.queue) / itemsPerPage)
                start = (page - 1) * itemsPerPage
                end = start + itemsPerPage
                queueList = ''
                queueDur = 0
                for index, track in enumerate(player.queue[start:end], start=start):
                    queueList += f'`{index+1}.` [{track.title}]({track.uri})\n'
                    queueDur += track.duration
                embed = discord.Embed(colour=0x93B1B4,
                                      description=f'{queueList}')
                queueDur = humanize.naturaldelta(
                    datetime.timedelta(milliseconds=queueDur))
                embed.set_footer(
                    text=f'Viewing page {page}/{pages} | Queue Duration: {queueDur} | Tracks: {len(player.queue)}')
                return await interaction.response.send_message(
                    embed=embed,
                    view=QueueButtons(self.bot, interaction.guild.id, page)
                )
            else:
                return await interaction.response.send_message(
                    content="Nothing playing.",
                    ephemeral=True
                )

    @Aoi.command(name="pause")
    async def pause(self, interaction: discord.Interaction):
        """Pauses or resumes the current player."""
        inVoice = await self.ensure_voice(interaction)
        if inVoice:
            player = self.bot.lavalink.player_manager.get(
                interaction.guild.id)
            if player.is_playing:
                if player.paused:
                    await player.set_pause(False)
                    return await interaction.response.send_message(
                        content="Resumed.",
                        ephemeral=True
                    )
                else:
                    await player.set_pause(True)
                    return await interaction.response.send_message(
                        content="Paused.",
                        ephemeral=True
                    )
            else:
                return await interaction.response.send_message(
                    content="Nothing playing.",
                    ephemeral=True
                )

    @Aoi.command(name="volume")
    @Aoi.describe(volume="The volume you want to set.")
    async def volume(self, interaction: discord.Interaction, volume: Aoi.Range[int, 1, 100] = None):
        """Changes or shows the current players volume."""
        inVoice = await self.ensure_voice(interaction)
        if inVoice:
            player = self.bot.lavalink.player_manager.get(
                interaction.guild.id)
            if player.is_playing:
                if volume is None:
                    return await interaction.response.send_message(
                        content=f'🔈 | {player.volume}%',
                        ephemeral=True
                    )
                await player.set_volume(volume)
                return await interaction.response.send_message(
                    content=f'🔈 | Set to {player.volume}%',
                    ephemeral=True
                )
            else:
                return await interaction.response.send_message(
                    content="Nothing playing.",
                    ephemeral=True
                )

    @Aoi.command(name="shuffle")
    async def shuffle(self, interaction: discord.Interaction):
        """Enables or disabled the players shuffle."""
        inVoice = await self.ensure_voice(interaction)
        if inVoice:
            player = self.bot.lavalink.player_manager.get(
                interaction.guild.id)
            if player.is_playing:
                player.shuffle = not player.shuffle
                return await interaction.response.send_message(
                    content='🔀 | Shuffle ' +
                    ('enabled' if player.shuffle else 'disabled'),
                    ephemeral=True
                )
            else:
                return await interaction.response.send_message(
                    content="Nothing playing.",
                    ephemeral=True
                )

    @Aoi.command(name="disconnect")
    async def disconnect(self, interaction: discord.Interaction):
        """Disconnect the bot from the voice channel."""
        inVoice = await self.ensure_voice(interaction)
        if inVoice:
            player = self.bot.lavalink.player_manager.get(
                interaction.guild.id)
            if not interaction.guild.voice_client:
                return await interaction.response.send_message(
                    content="Not connected.",
                    ephemeral=True
                )
            if not interaction.user.voice or (player.is_connected and interaction.user.voice.channel.id != int(player.channel_id)):
                return await interaction.response.send_message(
                    content="You're not in my voice channel!",
                    ephemeral=True
                )
            player.queue.clear()
            await player.stop()
            await interaction.guild.voice_client.disconnect(force=True)
            return await interaction.response.send_message(
                content="*⃣ | Disconnected.",
                ephemeral=True
            )

    @Aoi.command(name="lowpass")
    @Aoi.describe(strength="The strength of the lowpass filter.")
    async def lowpass(self, interaction: discord.Interaction, strength: int):
        """Sets the strength of the low pass filter."""
        inVoice = await self.ensure_voice(interaction)
        if inVoice:
            player = self.bot.lavalink.player_manager.get(
                interaction.guild.id)
            if strength == 1:
                return await interaction.response.send_message(
                    content="Strength must be greater than 1, but `0` to disable.",
                    ephemeral=True
                )
            strength = max(0.0, strength)
            strength = min(100, strength)
            if strength == 0.0:
                await player.remove_filter('lowpass')
                return await interaction.response.send_message(
                    content='Disabled **Low Pass Filter**',
                    ephemeral=True
                )
            low_pass = LowPass()
            low_pass.update(smoothing=strength)
            await player.set_filter(low_pass)
            await interaction.response.send_message(
                content=f'Set **Low Pass Filter** strength to {strength}.',
                ephemeral=True
            )

    @lowpass.error
    @disconnect.error
    @shuffle.error
    @volume.error
    @pause.error
    @queue.error
    @now.error
    @stop.error
    @skip.error
    @seek.error
    @liked.error
    @play.error
    async def send_error(self, interaction: discord.Interaction, error):
        self.bot.logger.error(f"[Music] Error: {error}")
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

    @lavalink.listener(lavalink.events.WebSocketClosedEvent)
    async def on_websocket_closed(self, event: lavalink.events.WebSocketClosedEvent):
        if event.code == 4014:
            data = await self.bot.db.musicChannel.find_one(
                {"_id": event.player.guild_id})
            if data:
                if event.player.fetch('channel') == data['channel']:
                    await self.edit_controller("queueEnd", event, data)
                else:
                    await self.delete_npMsg(event)
            else:
                await self.delete_npMsg(event)
            event.player.queue.clear()
            await event.player.stop()
            guild = self.bot.get_guild(event.player.guild_id)
            await guild.voice_client.disconnect(force=True)
            await self.bot.lavalink.player_manager.destroy(event.player.guild_id)

    @lavalink.listener(lavalink.events.QueueEndEvent)
    async def on_queue_end(self, event: lavalink.events.QueueEndEvent):
        data = await self.bot.db.musicChannel.find_one(
            {"_id": event.player.guild_id})
        if data:
            if event.player.fetch('channel') == data['channel']:
                await self.edit_controller("queueEnd", event, data)
            else:
                await self.delete_npMsg(event)
        await self.delete_npMsg(event)
        guild_id = event.player.guild_id
        guild = self.bot.get_guild(guild_id)
        await guild.voice_client.disconnect(force=True)

    @lavalink.listener(lavalink.events.TrackStartEvent)
    async def on_track_start(self, event: lavalink.events.TrackStartEvent):
        data = await self.bot.db.musicChannel.find_one(
            {"_id": event.player.guild_id})
        if data != None and data['toggle'] is True:
            if event.player.fetch('channel') == data['channel']:
                await self.edit_controller("trackStart", event, data)
            else:
                await self.send_controller(event)
        else:
            await self.send_controller(event)

    @lavalink.listener(lavalink.events.NodeConnectedEvent)
    async def on_node_connect(self, event: lavalink.events.NodeConnectedEvent):
        self.bot.logger.info(
            f"[Music] Connected to Lavalink node {event.node.name}")
        self.bot.richConsole.print(
            f"[bold green][Music][/] Connected to node {event.node.name}")

    @lavalink.listener(lavalink.events.NodeDisconnectedEvent)
    async def on_node_disconnect(self, event: lavalink.events.NodeDisconnectedEvent):
        self.bot.logger.info(
            f"[Music] Disconnected from node {event.node.name} with code {event.code}. Reason: {event.reason}")
        self.bot.richConsole.print(
            f"[bold red][Music][/] Disconnected from node {event.node.name} with code {event.code}. Reason: {event.reason}")

    async def delete_npMsg(self, event):
        if event.player.fetch('npMsg') != None:
            try:
                channel = self.bot.get_channel(event.player.fetch('channel'))
                msg = await channel.fetch_message(event.player.fetch('npMsg'))
                await msg.delete()
            except:
                pass

    async def send_controller(self, event):
        await self.delete_npMsg(event)
        if event.player.fetch('channel'):
            if event.track.stream:
                duration = '🔴 LIVE'
            else:
                dur = event.track.duration
                delta = datetime.timedelta(milliseconds=dur)
                duration = humanize.naturaldelta(delta)
            fmt = f'{event.track.title} - {event.track.author}' \
                if isinstance(event.track, SpotifyAudioTrack) else event.track.title
            song = f'**[{fmt}]({event.track.uri})**\n*Duration: {duration}*\n*Requested By: <@!{event.track.requester}>*'
            embed = discord.Embed(
                color=discord.Colour.teal(), title='Now Playing', description=song)
            if "open.spotify.com" in str(event.track.uri):
                url = f"https://open.spotify.com/oembed?url={event.track.uri}"
                async with request("GET", url) as response:
                    try:
                        json = await response.json()
                        embed.set_thumbnail(url=f"{json['thumbnail_url']}")
                    except:
                        pass
            else:
                embed.set_thumbnail(
                    url=f"https://img.youtube.com/vi/{event.track.identifier}/hqdefault.jpg")
            ch = self.bot.get_channel(event.player.fetch('channel'))
            npMsg = await ch.send(embed=embed, view=TrackStartEventButtons(self.bot, event.player.guild_id))
            event.player.store('npMsg', npMsg.id)

    async def edit_controller(self, type, event, data):
        channel = await self.bot.fetch_channel(data['channel'])
        message = await channel.fetch_message(data['message'])
        if type == "trackStart":
            if event.track.stream:
                duration = '🔴 LIVE'
            else:
                dur = event.track.duration
                delta = datetime.timedelta(milliseconds=dur)
                duration = humanize.naturaldelta(delta)
            fmt = f'{event.track.title} - {event.track.author}' \
                if isinstance(event.track, SpotifyAudioTrack) else event.track.title
            e = discord.Embed(colour=discord.Colour.teal())
            e.title = "Currently Playing:"
            e.description = f"**{fmt}**\n*[Link to Song]({event.track.uri})*"
            e.add_field(name="Duration:", value=duration)
            e.add_field(name="Requested By:",
                        value=f"<@!{event.track.requester}>")
            if event.player.queue:
                queueList = ''
                for index, track in enumerate(event.player.queue[0:5], start=0):
                    queueList += f'`{index+1}.` [{track.title}]({track.uri})\n'
                e.add_field(name="Queue List:", value=queueList, inline=False)
            else:
                e.add_field(
                    name="Queue List:", value="Join a voice channel and queue songs by name or url in here.",
                    inline=False)
            if "open.spotify.com" in str(event.track.uri):
                url = f"https://open.spotify.com/oembed?url={event.track.uri}"
                async with request("GET", url) as response:
                    try:
                        json = await response.json()
                        e.set_image(url=f"{json['thumbnail_url']}")
                    except:
                        pass
            else:
                e.set_image(
                    url=f"https://img.youtube.com/vi/{event.track.identifier}/hqdefault.jpg")
            return await message.edit(embed=e, view=PlayingButtons(self.bot, event.player.guild_id))
        elif type == "queueEnd":
            e = discord.Embed(
                colour=discord.Colour.teal(),
                description="Send a song link or query to start playing music!\nOr click the button to start you favorite songs!",
            )
            e.set_author(
                name=f"{self.bot.user.name} Music:",
                icon_url=self.bot.user.avatar
            )
            e.set_image(url=self.bot.user.avatar)
            return await message.edit(embed=e, view=DefaultButtons(self.bot))

    async def ensure_voice(self, interaction: discord.Interaction):
        try:
            player = self.bot.lavalink.player_manager.create(
                interaction.guild.id)
            should_connect = interaction.command.name in ('play', 'playlist')
            if not interaction.user.voice or not interaction.user.voice.channel:
                return await interaction.response.send_message(
                    content='Join a voicechannel first.',
                    ephemeral=True
                )

            v_client = interaction.guild.voice_client
            if not v_client:
                if not should_connect:
                    return await interaction.response.send_message(
                        content="Not connected.",
                        ephemeral=True
                    )

                permissions = interaction.user.voice.channel.permissions_for(
                    interaction.guild.me)
                if not permissions.connect or not permissions.speak:
                    return await interaction.response.send_message(
                        content="I need the `CONNECT` and `SPEAK` permissions.",
                        ephemeral=True
                    )

                player.store('channel', interaction.channel.id)
                await interaction.user.voice.channel.connect(cls=LavalinkVoiceClient, self_deaf=True)
                return True
            else:
                if v_client.channel.id != interaction.user.voice.channel.id:
                    return await interaction.response.send_message(
                        content="You need to be in my voice channel.",
                        ephemeral=True
                    )
                else:
                    return True
        except Exception as e:
            self.bot.logger.error(f"[Music] Error during ensure_voice: {e}")
            self.bot.richConsole.print(
                f"[bold red][Music][/] Error during ensure_voice: {e}")

    def reload_sources(self):
        self.bot.lavalink.sources.clear()
        self.bot.lavalink.register_source(SpotifySource(
            self.bot.config['spotify']['id'], self.bot.config['spotify']['secret']))

    def cog_unload(self):
        """ Cog unload handler. This removes any event hooks that were registered. """
        self.bot.lavalink._event_hooks.clear()


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(Music(bot))
