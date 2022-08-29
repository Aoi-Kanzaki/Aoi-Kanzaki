import math
import re
import aiosqlite
import discord
import lavalink
from aiohttp import request
from discord.ext import commands
from lavalink.models import AudioTrack
from lavalink.utils import format_time
from utils._Spotify import SpotifySource
from utils._LavalinkVoiceClient import LavalinkVoiceClient
from utils._MusicButtons import event_hook, np_msg, queue_msg, search_msg
from lavalink.events import QueueEndEvent, TrackExceptionEvent, TrackStartEvent, TrackEndEvent, NodeConnectedEvent

url_rx = re.compile(r'https?:\/\/(?:www\.)?.+')

class Music(commands.Cog):
    def __init__(self, bot):
        fresh = bot.tree
        self.bot = bot
        self.spotify_token = None
        if not hasattr(bot, 'lavalink'):
            bot.lavalink = lavalink.Client(bot.user.id)
            bot.lavalink.add_node(
                host='127.0.0.1',
                port=2333,
                password='youshallnotpass',
                region='na',
                name='default-node',
                resume_timeout=None,
                reconnect_attempts=3
            )
        bot.lavalink._event_hooks.clear()
        bot.lavalink.add_event_hooks(self)
        self.reload_sources()

        @fresh.command(name="play")
        async def play(interaction: discord.Interaction, query: str):
            """ Searches and plays a song from a given query. """
            checkVoice = await self.ensure_voice(interaction)
            if checkVoice:
                player = self.bot.lavalink.player_manager.players.get(interaction.guild.id)
                query = query.strip('<>')
                e = discord.Embed(color=discord.Color.blurple())
                if not url_rx.match(query) and not query.startswith('spotify:'):
                    query = f'spsearch:{query}'

                results = await self.bot.lavalink.get_tracks(query, check_local=True)

                if not results or not results.tracks:
                    return await interaction.response.send_message('Nothing found.')

                if results.load_type == 'PLAYLIST_LOADED':
                    tracks = results.tracks
                    for track in tracks:
                        player.add(requester=interaction.user.id, track=track)
                    e.title = "Playlist Enqueued!"
                    e.description = f"{results.playlist_info.name} with {len(tracks)} tracks."
                    await interaction.response.send_message(embed=e, ephemeral=True)
                    
                else:
                    track = results.tracks[0]
                    player.add(requester=interaction.user.id, track=track)
                    if player.queue:
                        e.title = "Track Enqueued!"
                        e.description = f"{track.title}\n{track.uri}"
                        await interaction.response.send_message(embed=e, ephemeral=True)
                player.store('channel', interaction.channel.id)
                if not player.is_playing:
                    await player.play()

        @fresh.command(name="pause")
        async def pause(interaction: discord.Interaction):
            """Pauses or resumes music playback."""
            checkVoice = await self.ensure_voice(interaction)
            if checkVoice:
                player = self.bot.lavalink.player_manager.get(interaction.guild.id)

                if not player.is_playing:
                    return await interaction.response.send_message(
                        "<:tickNo:697759586538749982> Nothing playing, use `play <song_name>`.", ephemeral=True
                    )

                await player.set_pause(not player.paused)
                return await interaction.response.send_message("Done.", ephemeral=True)

        @fresh.command(name="queue")
        @commands.cooldown(1, 5, commands.BucketType.guild)
        async def queue(interaction: discord.Interaction, page: int=1):
            """Shows you all the songs in queue."""
            checkVoice = await self.ensure_voice(interaction)
            if checkVoice:
                player = self.bot.lavalink.player_manager.get(interaction.guild.id)
                if not player.queue:
                    return await interaction.response.send_message(
                        '<:tickNo:697759586538749982> Nothing playing.', ephemeral=True)
                if player.current.stream:
                    dur = 'LIVE'
                else:
                    dur = format_time(player.current.duration)
                pos = format_time(player.position)
                e = discord.Embed(colour=discord.Color.blurple())
                e.add_field(
                    name="Currently Playing:",
                    value=f"{player.current.title}\n{player.current.uri}\n{await self.draw_time(interaction.guild.id)} `[{pos}/{dur}]`"
                )
                e.add_field(
                    name="Up Next:",
                    value=f"{await self.draw_queue(interaction.guild.id, page)}", inline=False
                )
                e.set_thumbnail(url=f'https://img.youtube.com/vi/{player.current.identifier}/hqdefault.jpg')
                if len(player.queue) > 10:
                    e.set_footer(text=f'Page {page}/{math.ceil(len(player.queue) / 10)} | {len(player.queue)} tracks')
                    return await interaction.response.send_message(embed=e, view=queue_msg(self.bot, interaction.guild.id, 1))
                else:
                    return await interaction.response.send_message(embed=e)

        @fresh.command(name="previous")
        @commands.cooldown(1, 5, commands.BucketType.guild)
        async def previous(interaction: discord.Interaction):
            """Returns to the previous song that played."""
            checkVoice = await self.ensure_voice(interaction)
            if checkVoice:
                player = self.bot.lavalink.player_manager.get(interaction.guild.id)
                if player.fetch("prev_song") is None:
                    return await interaction.response.send_message(
                        "<:tickNo:697759586538749982> No previous track.", ephemeral=True)
                last_track = await player.node.get_tracks(player.fetch("prev_song"))
                if not last_track:
                    return await interaction.response.send_message(
                        "<:tickNo:697759586538749982> Seems there was an issue in getting the last track and nothing was found.",
                        ephemeral=True
                    )
                player.add(
                    requester=player.fetch("prev_requester"),
                    track=AudioTrack(last_track['tracks'][0],player.fetch("prev_requester"),recommended=True)
                    )
                player.queue.insert(0, player.queue[-1])
                player.queue.pop(len(player.queue))
                await player.skip()
                player.store("prev_requester", None)
                player.store("prev_song", None)
                player.store("playing_song", None)
                player.store("requester", None)
                embed = discord.Embed(
                    colour=discord.Color.blurple(), title="Replaying Track",
                    description=f"**[{player.current.title}]({player.current.uri})**"
                    )
                return await interaction.response.send_message(embed=embed, ephemeral=True)

        @fresh.command(name="volume")
        @commands.cooldown(1, 5, commands.BucketType.guild)
        async def volume(interaction: discord.Interaction, volume: int=None):
            """Changes volume of the player."""
            checkVoice = await self.ensure_voice(interaction)
            if checkVoice:
                player = self.bot.lavalink.player_manager.get(interaction.guild.id)
                if not volume:
                    return await interaction.response.send_message(f'🔈 | {player.volume}%', ephemeral=True)
                if volume > 100:
                    volume = 100
                await player.set_volume(volume)
                return await interaction.response.send_message(f'🔈 | Set to {player.volume}%', ephemeral=True)

        @fresh.command(name="search")
        @commands.cooldown(1, 5, commands.BucketType.guild)
        async def search(interaction: discord.Interaction, query: str):
            """Search for something to play."""
            checkVoice = await self.ensure_voice(interaction)
            if checkVoice:
                results = await self.bot.lavalink.get_tracks(f'ytsearch:{query}')
                if not results or not results['tracks']:
                    return await interaction.response.send_message(
                        '<:tickNo:697759586538749982> Nothing found!', ephemeral=True)
                else:
                    e = discord.Embed(color=discord.Color.blurple())
                    e.title = 'Search Results'
                    e.description = f'{results["tracks"][0]["info"]["title"]}\n{results["tracks"][0]["info"]["uri"]}'
                    e.add_field(name="Author", value=results["tracks"][0]["info"]["author"])
                    e.add_field(name="Duration", value=format_time(results["tracks"][0]["info"]["duration"]))
                    picID = results["tracks"][0]["info"]["identifier"]
                    e.set_thumbnail(url=f"https://img.youtube.com/vi/{picID}/hqdefault.jpg")
                    await interaction.response.send_message(
                        embed=e, view=search_msg(self.bot, interaction.guild.id, results))

        @fresh.command(name="disconnect")
        async def disconnect(interaction: discord.Interaction):
            """Disconnects from current voice channel."""
            checkVoice = await self.ensure_voice(interaction)
            if checkVoice:
                player = self.bot.lavalink.player_manager.get(interaction.guild.id)
                if player.is_connected:
                    if player.fetch('npmsg') != None:
                        try:
                            msg = await self.bot.get_channel(player.fetch('channel')).fetch_message(player.fetch('npmsg'))
                            await msg.delete()
                        except:
                            pass
                    await interaction.guild.voice_client.disconnect(force=True)
                    await interaction.response.send_message("Disconnected...", ephemeral=True)
                    return self.bot.lavalink.player_manager.remove(interaction.guild.id)
                else:
                    return await interaction.response.send_message(
                        '<:tickNo:697759586538749982> Not connected in this server.', ephemeral=True)

        @fresh.command(name="jump")
        @commands.cooldown(1, 5, commands.BucketType.guild)
        async def jump(interaction: discord.Interaction, number: int):
            """Moves song number specifed to the top of the queue."""
            checkVoice = await self.ensure_voice(interaction)
            if checkVoice:
                player = self.bot.lavalink.player_manager.get(interaction.guild.id)
                if not player.queue:
                    await interaction.response.send_message(
                        '<:tickNo:697759586538749982> Nothing queued.', ephemeral=True)
                if number > len(player.queue) or number < 1:
                    await interaction.response.send_message(
                        '<:tickNo:697759586538749982> Song number must be greater than 1 and within the queue limit.', ephemeral=True)
                player.queue.insert(0, self.bot.lavalink.player_manager.get(interaction.guild.id).queue[number-1])
                player.queue.pop(number)
                return await interaction.response.send_message(
                    '<:tickYes:697759553626046546> Moved to the top of the queue.', ephemeral=True)

        @fresh.command(name="clear")
        async def clear(interaction: discord.Interaction):
            """Clears the queue, doesn't stop the player tho."""
            checkVoice = await self.ensure_voice(interaction)
            if checkVoice:
                player = self.bot.lavalink.player_manager.get(interaction.guild.id)
                if not player.queue:
                    await interaction.response.send_message(
                        "<:tickNo:697759586538749982> Nothing queued, use `play <song_name>`.", ephemeral=True)
                    return
                else:
                    player.queue.clear()
                    return await interaction.response.send_message(
                        "<:tickYes:697759553626046546> Cleared queue.", ephemeral=True)

        @fresh.command(name="stop")
        async def stop(interaction: discord.Interaction):
            """Stops playback of the song and clears the queue."""
            checkVoice = await self.ensure_voice(interaction)
            if checkVoice:
                player = self.bot.lavalink.player_manager.get(interaction.guild.id)
                if player.is_playing:
                    await interaction.response.send_message('Stopping...', ephemeral=True)
                    player.queue.clear()
                    await player.stop()

        @fresh.command(name="remove")
        async def remove(interaction: discord.Interaction, index: int):
            """Remove a specific song number from the queue."""
            checkVoice = await self.ensure_voice(interaction)
            if checkVoice:
                player = self.bot.lavalink.player_manager.get(interaction.guild.id)
                if not player.queue:
                    return await interaction.response.send_message(
                        "<:tickNo:697759586538749982> Nothing queued, use `play <song_name>`.", ephemeral=True)
                if index > len(player.queue) or index < 1:
                    return await interaction.response.send_message(
                        '<:tickNo:697759586538749982> Song number must be greater than 1 and within the queue limit.', ephemeral=True)
                player.queue.pop(index-1)
                return await interaction.response.send_message(
                    '<:tickYes:697759553626046546> Removed from the queue.', ephemeral=True)

        @fresh.command(name="nowplaying")
        async def nowplaying(interaction: discord.Interaction):
            """Shows you the song currently playing."""
            checkVoice = await self.ensure_voice(interaction)
            if checkVoice:
                player = self.bot.lavalink.player_manager.get(interaction.guild.id)
                if player.is_playing:
                    if player.current:
                        if player.current.stream:
                            dur = 'LIVE'
                        else:
                            dur = format_time(player.current.duration)
                    e = discord.Embed(colour=discord.Color.blurple())
                    e.title = "Now Playing:"
                    e.description = f"{player.current.title}\n"
                    e.description += f"{await self.draw_time(interaction.guild.id)} `[{format_time(player.position)}/{dur}]`\n"
                    e.description += f"{player.current.uri}\n"
                    e.set_thumbnail(url=f'https://img.youtube.com/vi/{player.current.identifier}/hqdefault.jpg')
                    await interaction.response.send_message(embed=e, view=np_msg(self.bot, interaction.guild.id))
                else:
                    if player.is_connected:
                        return await interaction.response.send_message(
                            "<:tickNo:697759586538749982> Nothing is playing.", ephemeral=True)

        @fresh.command(name="skip")
        async def skip(interaction: discord.Interaction, number: int=None):
            """Skips to the next track in the queue."""
            checkVoice = await self.ensure_voice(interaction)
            if checkVoice:
                player = self.bot.lavalink.player_manager.get(interaction.guild.id)
                if player.current is None:
                    return await interaction.response.send_message(
                        "<:tickNo:697759586538749982> Nothing playing, use `play <song_name>`.", ephemeral=True)
                if number is not None:
                    results = await self.bot.lavalink.get_tracks(player.queue[number-1].uri)
                    player.add(requester=interaction.user.id, track=results['tracks'][0])
                    player.queue.insert(0, self.bot.lavalink.player_manager.get(interaction.guild.id).queue[len(player.queue) - 1])
                    player.queue.pop(number)
                    return await player.skip()
                else:
                    return await player.skip()

    @lavalink.listener(TrackStartEvent)
    async def on_track_start(self, event: TrackStartEvent):
        async with aiosqlite.connect("./data/music.db") as db:
            try:
                getData = await db.execute(
                    "SELECT musicMessage, musicToggle, musicChannel, musicRunning FROM musicSettings WHERE guild = ?", 
                    (event.player.guild_id,)
                )
                data = await getData.fetchone()
            except:
                pass
            playing_song = event.player.fetch("playing_song")
            requester = event.player.fetch("requester")
            event.player.store("prev_song", playing_song)
            event.player.store("prev_requester", requester)
            event.player.store("playing_song", event.player.current.uri)
            event.player.store("requester", event.player.current.requester)
            channel = event.player.fetch('channel')
            if event.player.fetch('channel'):
                if data[2] == event.player.fetch('channel'):
                    if event.player.queue:
                        queue_list = ''
                        for i, track in enumerate(event.player.queue[(1 - 1) * 5:(1 - 1) * 5 + 5], start=(1 - 1) * 5):
                            queue_list += '`{}.` {}\n'.format(i + 1, track.title)
                    else:
                        queue_list = "Join a voice channel and queue songs by name or url in here."
                    if event.player.current.stream:
                        dur = 'LIVE'
                    else:
                        dur = format_time(event.player.current.duration)
                    e = discord.Embed(color=discord.Color.blurple())
                    kek = f"{event.player.current.title}\n{event.player.current.uri}"
                    e.add_field(name="Currently Playing:", value=kek, inline=False)
                    e.add_field(name="Author:", value=event.player.current.author)
                    e.add_field(name="Duration:", value=dur)
                    e.add_field(name="Queue List:", value=queue_list, inline=False)
                    if "open.spotify.com" in str(event.player.current.uri):
                        url = f"https://open.spotify.com/oembed?url={event.player.current.uri}"
                        async with request("GET", url) as response:
                            json = await response.json()
                            e.set_image(url=f"{json['thumbnail_url']}")
                    else:
                        e.set_image(url=f"https://img.youtube.com/vi/{event.player.current.identifier}/hqdefault.jpg")
                    requester = self.bot.get_user(event.player.current.requester)
                    e.set_footer(text=f"Requested by {requester.name}#{requester.discriminator}")
                    channel = await self.bot.fetch_channel(data[2])
                    msg = await channel.fetch_message(data[0])
                    await msg.edit(embed=e, view=event_hook(self.bot, int(event.player.guild_id)))
                else:
                    if event.player.fetch('npmsg') != None:
                        try:
                            msg = await self.bot.get_channel(event.player.fetch('channel')).fetch_message(event.player.fetch('npmsg'))
                            await msg.delete()
                        except:
                            pass
                    if self.bot.get_channel(event.player.fetch('channel')):
                        try:
                            e = discord.Embed(colour=discord.Color.blurple())
                            e.title = "Now Playing:"
                            e.description = f"{event.player.current.title}\n"
                            e.description += f"{event.player.current.uri}\n"
                            if "open.spotify.com" in str(event.player.current.uri):
                                url = f"https://open.spotify.com/oembed?url={event.player.current.uri}"
                                async with request("GET", url) as response:
                                    json = await response.json()
                                    e.set_thumbnail(url=f"{json['thumbnail_url']}")
                            else:
                                e.set_thumbnail(url=f"https://img.youtube.com/vi/{event.player.current.identifier}/hqdefault.jpg")
                            if event.player.queue:
                                number = 0
                                upNext = ""
                                for track in event.player.queue[0:5]:
                                    number += 1
                                    upNext += f"`{number})` {track.title}\n"
                                e.add_field(name="Up Next:", value=upNext)
                            message = await self.bot.get_channel(event.player.fetch('channel')).send(embed=e, view=event_hook(self.bot, int(event.player.guild_id)))
                            event.player.store('npmsg', message.id)
                        except:
                            pass

    @lavalink.listener(TrackEndEvent)
    async def on_track_end(self, event: TrackEndEvent):
        if event.player.fetch('npmsg') != None:
            try:
                msg = await self.bot.get_channel(event.player.fetch('channel')).fetch_message(event.player.fetch('npmsg'))
                await msg.delete()
            except discord.errors.NotFound:
                pass

    @lavalink.listener(QueueEndEvent)
    async def on_queue_end(self, event: QueueEndEvent):
        async with aiosqlite.connect("./data/music.db") as db:
            try:
                getData = await db.execute(
                    "SELECT musicMessage, musicToggle, musicChannel, musicRunning FROM musicSettings WHERE guild = ?",
                    (event.player.guild_id,)
                )
                data = await getData.fetchone()
            except:
                pass
            if event.player.fetch('channel') == data[2]:
                channel = await self.bot.fetch_channel(data[2])
                msg = await channel.fetch_message(data[0])
                e = discord.Embed(color=discord.Color.blurple())
                e.title = "Nothing Currently Playing:"
                e.description = "Send a song `link` or `query` to play."
                e.description += "\nSend `pause` or `resume` to control the music."
                e.description += "\nSend `skip` to skip the current song."
                e.description += "\nSend `dc` or `disconnect` to disconnect from the voice channel."
                e.description += "\nSend `vol 10` or `volume 10` to change the volume."
                e.description += "\nSend `rem 1` or `remove 1` to remove a song from the queue."
                e.description += "\nSend `search <query>` to search for a song."
                e.set_image(url="https://i.imgur.com/VIYaATs.jpg")
                await msg.edit(embed=e, view=None)
            await self.bot.get_guild(int(event.player.guild_id)).voice_client.disconnect(force=True)
            self.bot.lavalink.player_manager.remove(event.player.guild_id)

    @lavalink.listener(NodeConnectedEvent)
    async def on_node_connected(self, event: NodeConnectedEvent):
        self.bot.logger.info(f"Lavalink succesfully connected to node: {event.node.name}")

    @lavalink.listener(TrackExceptionEvent)
    async def on_track_exception(self, event: TrackExceptionEvent):
        self.bot.logger.info(f"Lavalink encountered an error on track: {event.track}\n{event.exception}")

    async def draw_queue(self, guild_id, page: int=1):
        player = self.bot.lavalink.player_manager.get(guild_id)
        queue_list = ''
        for i, track in enumerate(player.queue[(page - 1) * 10:(page - 1) * 10 + 10], start=(page - 1) * 10):
            queue_list += '{}) {}\n'.format(i + 1, track.title)
        return queue_list

    async def draw_time(self, guild_id):
        player = self.bot.lavalink.player_manager.get(guild_id)
        if player.paused:
            msg = r'\⏸ '
        else:
            msg = r'\▶ '
        for i in range(12):
            if i == round((player.position / player.current.duration) * 12):
                msg += r'\🔘'
            else:
                msg += '\N{BOX DRAWINGS HEAVY HORIZONTAL}'
        return msg

    def reload_sources(self):
        self.bot.lavalink.sources.clear()
        self.bot.lavalink.register_source(SpotifySource(self.bot.spotify_id, self.bot.spotify_secret))

    async def cog_unload(self):
        self.bot.lavalink._event_hooks.clear()

    async def ensure_voice(self, interaction: discord.Interaction):
        try:
            player = self.bot.lavalink.player_manager.create(interaction.guild.id, endpoint="us")
        except Exception as error:
            if isinstance(error, lavalink.errors.NodeError):
                await interaction.response.send_message(
                    "<:tickNo:697759586538749982> There is no avaliable nodes right now! Try again later.", ephemeral=True)
                self.bot.logger.error(f"Tried to join a voice channel in {interaction.guild.name} but there are no avaliable nodes.")
                return False
        if not interaction.user.voice or not interaction.user.voice.channel:
            await interaction.response.send_message(
                '<:tickNo:697759586538749982> Join a voicechannel first.', ephemeral=True)
            self.bot.logger.info(f"Tried to join {interaction.user} voicechannel but they are not in one.")
            return False
        if not player.is_connected:
            if (not interaction.user.voice.channel.permissions_for(interaction.guild.me).connect or not 
                    interaction.user.voice.channel.permissions_for(interaction.guild.me).speak):
                await interaction.response.send_message(
                    '<:tickNo:697759586538749982> I need the `CONNECT` and `SPEAK` permissions.', ephemeral=True)
                self.bot.logger.info(f"Tried to join {interaction.user} voicechannel but I don't have the permissions.")
                return False
            player.store('channel', interaction.channel.id)
            await interaction.user.voice.channel.connect(cls=LavalinkVoiceClient)
            return True
        else:
            if int(player.channel_id) != interaction.user.voice.channel.id:
                await interaction.response.send_message(
                    '<:tickNo:697759586538749982> You need to be in my voicechannel.', ephemeral=True)
                return False
            return True

async def setup(bot):
    await bot.add_cog(Music(bot))