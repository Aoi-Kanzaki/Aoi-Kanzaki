import base64
import time
import re
import math
import asyncio
import discord
import lavalink
import aiosqlite
from colr import color
from lavalink.utils import format_time
from lavalink.models import AudioTrack
from discord.ext import commands
from utils._LavalinkVoiceClient import LavalinkVoiceClient
from utils._MusicButtons import event_hook_buttons, queue_msg_buttons, np_msg_buttons

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spotify_token = None
        if not hasattr(bot, 'lavalink'):
            bot.lavalink = lavalink.Client(bot.user.id)
            bot.lavalink.add_node(host='127.0.0.1', port=2333, password='youshallnotpass', region='eu', name='default-node', resume_timeout=None, reconnect_attempts=3)
        lavalink.add_event_hook(self.track_hook)

    async def cog_load(self):
        async with aiosqlite.connect("./data/music.db") as db:
            await db.execute("CREATE TABLE IF NOT EXISTS musicSettings (musicMessage INTEGER, musicToggle INTEGER, musicChannel INTEGER, musicRunning INTEGER, guild INTEGER)")
            await db.commit()

    async def cog_unload(self):
        self.bot.lavalink._event_hooks.clear()
        async with aiosqlite.connect("./data/music.db") as db:
            for guild in self.bot.guilds:
                try:
                    getData = await db.execute("SELECT musicMessage, musicToggle, musicChannel, musicRunning FROM musicSettings WHERE guild = ?", (guild.id,))
                    data = await getData.fetchone()
                    if data[1] ==1:
                        channel = await guild.fetch_channel(data[2])
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
                        await asyncio.sleep(1)
                except Exception as e:
                    print(e)

    async def cog_before_invoke(self, ctx):
        if ctx.guild is not None:
            return await self.ensure_voice(ctx)
        return ctx.guild is not None

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            print(color(f"Error in command {ctx.command.name}\n{error}", fore=self.bot.colors["red"]))

    async def ensure_voice(self, ctx):
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, endpoint="us")
        if ctx.command.name in ('play', 'search'):
            if not ctx.author.voice or not ctx.author.voice.channel:
                return await ctx.send('<:tickNo:697759586538749982> Join a voicechannel first.', delete_after=5)
            if not player.is_connected:
                if not ctx.author.voice.channel.permissions_for(ctx.me).connect or not ctx.author.voice.channel.permissions_for(ctx.me).speak:
                    return await ctx.send('<:tickNo:697759586538749982> I need the `CONNECT` and `SPEAK` permissions.', delete_after=5)
                player.store('channel', ctx.channel.id)
                await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient)
            else:
                if int(player.channel_id) != ctx.author.voice.channel.id:
                    return await ctx.send('<:tickNo:697759586538749982> You need to be in my voicechannel.', delete_after=5)

    async def track_hook(self, event):
        async with aiosqlite.connect("./data/music.db") as db:
            try:
                getData = await db.execute("SELECT musicMessage, musicToggle, musicChannel, musicRunning FROM musicSettings WHERE guild = ?", (event.player.guild_id,))
                data = await getData.fetchone()
            except:
                pass
        if not hasattr(event, 'player'):
            return
        if isinstance(event, lavalink.events.NodeConnectedEvent):
            print(color(f"Lavalink succesfully connected to node:", fore=self.bot.colors['cyan']), color(f"{event.node.name}", fore=self.bot.colors['purple']))
        if isinstance(event, lavalink.events.QueueEndEvent):
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
        if isinstance(event, lavalink.events.TrackEndEvent):
            if event.player.fetch('npmsg') != None:
                try:
                    msg = await self.bot.get_channel(event.player.fetch('channel')).fetch_message(event.player.fetch('npmsg'))
                    await msg.delete()
                except discord.errors.NotFound:
                    pass
        if isinstance(event, lavalink.events.TrackStartEvent):
            playing_song = event.player.fetch("playing_song")
            requester = event.player.fetch("requester")
            event.player.store("prev_song", playing_song)
            event.player.store("prev_requester", requester)
            event.player.store("playing_song", event.player.current.uri)
            event.player.store("requester", event.player.current.requester)
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
                    e.set_image(url=f"https://img.youtube.com/vi/{event.player.current.identifier}/hqdefault.jpg")
                    requester = self.bot.get_user(event.player.current.requester)
                    e.set_footer(text=f"Requested by {requester.name}#{requester.discriminator}")
                    channel = await self.bot.fetch_channel(data[2])
                    msg = await channel.fetch_message(data[0])
                    await msg.edit(embed=e, view=event_hook_buttons(self.bot, int(event.player.guild_id)))
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
                            e.set_thumbnail(url=f'https://img.youtube.com/vi/{event.player.current.identifier}/hqdefault.jpg')
                            if event.player.queue:
                                number = 0
                                upNext = ""
                                for track in event.player.queue[0:5]:
                                    number += 1
                                    upNext += f"`{number})` {track.title}\n"
                                e.add_field(name="Up Next:", value=upNext)
                            message = await self.bot.get_channel(event.player.fetch('channel')).send(embed=e, view=event_hook_buttons(self.bot, int(event.player.guild_id)))
                            event.player.store('npmsg', message.id)
                        except:
                            pass

    @commands.hybrid_command()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    @commands.has_permissions(manage_guild=True)
    async def setup(self, ctx):
        """Toggles the music channel on and off."""
        existing_channels = [e.name for e in ctx.guild.channels]
        async with aiosqlite.connect("./data/music.db") as db:
            getData = await db.execute("SELECT musicToggle, musicChannel FROM musicSettings WHERE guild = ?", (ctx.guild.id,))
            data = await getData.fetchone()
            if data is None:
                if "fresh-music" in existing_channels:
                    return await ctx.send("<:tickNo:697759586538749982> Please delete the `fresh-music` channel first.", delete_after=5)
                created = await ctx.guild.create_text_channel(name="fresh-music", topic="THIS IS IN BETA, PLEASE REPORT BUGS TO Jonny#0181")
                msgid = await self.send_player_msg(created.id)
                await db.execute("INSERT INTO musicSettings (musicMessage, musicToggle, musicChannel, musicRunning, guild) VALUES (?, ?, ?, ?, ?)", (msgid, 1, created.id, 0, ctx.guild.id,))
                await ctx.send("<:tickYes:697759553626046546> Music channel setup complete. You can now move the channel to wherever you want.")
            elif data[0] == 1:
                if "fresh-music" in existing_channels:
                    channel = await ctx.guild.fetch_channel(data[1])
                    await channel.delete()
                    await db.execute("UPDATE musicSettings SET musicToggle = ? WHERE guild = ?", (0, ctx.guild.id,))
                    await ctx.send("<:tickYes:697759553626046546> Deleted fresh music channel and disabled the system.")
                else:
                    await db.execute("UPDATE musicSettings SET musicToggle = ? WHERE guild = ?", (0, ctx.guild.id,))
                    await ctx.send("<:tickYes:697759553626046546> The fresh music channel has already been deleted. But I disabled the system.")
            else:
                if "fresh-music" in existing_channels:
                    channelid = [e.id for e in ctx.guild.channels if e.name == 'fresh-music'][0]
                    msgid = await self.send_player_msg(channelid)
                    await db.execute("UPDATE musicSettings SET musicMessage = ?, musicToggle = ?, musicChannel = ? WHERE guild = ?", (msgid, 1, channelid, ctx.guild.id,))
                    await ctx.send("<:tickYes:697759553626046546> Music channel setup complete. You can now move the channel to wherever you want.")
                else:
                    created = await ctx.guild.create_text_channel(name="fresh-music", topic="THIS IS IN BETA, PLEASE REPORT BUGS TO Jonny#0181")
                    msgid = await self.send_player_msg(created.id)
                    await db.execute("UPDATE musicSettings SET musicMessage = ?, musicToggle = ?, musicChannel = ? WHERE guild = ?", (msgid, 1, created.id, ctx.guild.id,))
                    await ctx.send(f"<:tickYes:697759553626046546> Music channel setup complete. You can now move <#{created.id}> to wherever you want.")
            await db.commit()
            
    async def send_player_msg(self, channelid):
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
        msg = await self.bot.get_channel(channelid).send(embed=e)
        return msg.id

    @commands.hybrid_command(aliases=['p'])
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def play(self, ctx, *, query: str):
        """ Searches and plays a song from a given query. """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        query = query.strip('<>')
        if "open.spotify.com" in query:
            query = "{}".format(re.sub(r"(http[s]?:\/\/)?(open.spotify.com)\/", "", query).replace("/", ":"))
            await self.queue_spotify(ctx, player, query)
        if not re.compile(r'https?://(?:www\.)?.+').match(query):
            query = f'ytsearch:{query}'
        results = await player.node.get_tracks(query)
        if not results or not results['tracks']:
            return await ctx.send('Nothing found!', delete_after=5)
        embed = discord.Embed(color=discord.Color.blurple())
        if results['loadType'] == 'LOAD_FAILED':
            await ctx.voice_client.disconnect(force=True)
            self.bot.lavalink.player_manager.remove(ctx.guild.id)
            return await ctx.send('Oh no, something failed. Please try again.', delete_after=5)
        if results['loadType'] == 'PLAYLIST_LOADED':
            tracks = results['tracks']
            for track in tracks:
                player.add(requester=ctx.author.id, track=track)
            embed.title = 'Playlist Enqueued!'
            embed.description = f'{results["playlistInfo"]["name"]} - {len(tracks)} tracks'
            if not player.is_playing:
                await player.play()
            await ctx.send(embed=embed, delete_after=5)
        else:
            track = results['tracks'][0]
            embed.title = 'Track Enqueued'
            embed.description = f'[{track["info"]["title"]}]({track["info"]["uri"]})'
            track = AudioTrack(track, ctx.author.id, recommended=True)
            player.add(requester=ctx.author.id, track=track)
            if not player.is_playing:
                await player.play()
            await ctx.send(embed=embed, delete_after=5)

    @commands.hybrid_command(aliases=["prev"])
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def previous(self, ctx):
        """Returns to the previous song that played."""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if player.fetch("prev_song") is None:
            return await ctx.send("<:tickNo:697759586538749982> No previous track.", delete_after=5)
        last_track = await player.node.get_tracks(player.fetch("prev_song"))
        if not last_track:
            return await ctx.send("<:tickNo:697759586538749982> Seems there was an issue in getting the last track and nothing was found.", delete_after=5)
        player.add(requester=player.fetch("prev_requester"), track=AudioTrack(last_track['tracks'][0], player.fetch("prev_requester"), recommended=True))
        player.queue.insert(0, player.queue[-1])
        player.queue.pop(len(player.queue))
        await player.skip()
        player.store("prev_requester", None)
        player.store("prev_song", None)
        player.store("playing_song", None)
        player.store("requester", None)
        embed = discord.Embed(colour=discord.Color.blurple(), title="Replaying Track", description=f"**[{player.current.title}]({player.current.uri})**")
        return await ctx.send(embed=embed, delete_after=5)

    @commands.hybrid_command(aliases=['vol'])
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def volume(self, ctx, volume: int=None):
        """Changes volume of the player."""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not volume:
            return await ctx.send(f'🔈 | {player.volume}%', delete_after=5)
        if volume > 100:
            volume = 100
        await player.set_volume(volume)
        return await ctx.send(f'🔈 | Set to {player.volume}%', delete_after=5)

    @commands.hybrid_command()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def search(self, ctx, query):
        """Search for something to play."""
        results = await self.bot.lavalink.get_tracks(f'ytsearch:{query}')
        if not results or not results['tracks']:
            return await ctx.send('<:tickNo:697759586538749982> Nothing found!', delete_after=5)
        number = 0
        e = discord.Embed()
        e.colour = discord.Color.blurple()
        e.description = ""
        for r in results['tracks']:
            number += 1
            e.description += f"**{number})** {r['info']['title']}\n"
        e.description += "\nPlease choose a result. Examples: `start 1` to play, `cancel` to cancel this search and delete messages."
        m = await ctx.send(embed=e)
        def check(m):
            return m.channel == ctx.channel and m.author == ctx.author
        while True:
            try:
                msg = await ctx.bot.wait_for('message', check=check, timeout=60.0)
            except asyncio.TimeoutError:
                return
            if msg.content in ("cancel", "Cancel"):
                return await m.delete()
            elif msg.content.startswith('start') or msg.content.startswith('Start'):
                content = msg.content.replace('start ', '').replace('Start ', '')
                if content.isdigit():
                    if int(content) > number:
                        await ctx.send("<:tickNo:697759586538749982> Invalid number, try again.", delete_after=2)
                    else:
                        await m.delete()
                        return await ctx.invoke(self.bot.get_command('play'), query=results['tracks'][int(content) - 1]['info']['uri'])

    @commands.hybrid_command(aliases=['dc'])
    async def disconnect(self, ctx):
        """Disconnects from current voice channel."""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if player.is_connected:
            await ctx.voice_client.disconnect(force=True)
            await ctx.send("Disconnected...", delete_after=5)
            return self.bot.lavalink.player_manager.remove(ctx.guild.id)
        else:
            return await ctx.send('<:tickNo:697759586538749982> Not connected in this server.', delete_after=5)

    @commands.hybrid_command()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def jump(self, ctx, number: int):
        """Moves song number specifed to the top of the queue."""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.queue:
            await ctx.send('<:tickNo:697759586538749982> Nothing queued.', delete_after=5)
        if number > len(player.queue) or number < 1:
            await ctx.send('<:tickNo:697759586538749982> Song number must be greater than 1 and within the queue limit.', delete_after=5)
        player.queue.insert(0, self.bot.lavalink.player_manager.get(ctx.guild.id).queue[number-1])
        player.queue.pop(number)
        return await ctx.send('<:tickYes:697759553626046546> Moved to the top of the queue.', delete_after=10)

    @commands.hybrid_command()
    async def clear(self, ctx):
        """Clears the queue, doesn't stop the player tho."""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.queue:
            await ctx.send("<:tickNo:697759586538749982> Nothing queued, use `play <song_name>`.", delete_after=5)
            return
        else:
            player.queue.clear()
            return await ctx.send("<:tickYes:697759553626046546> Cleared queue.", delete_after=10)

    @commands.hybrid_command()
    async def stop(self, ctx):
        """Stops playback of the song and clears the queue."""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if player.is_playing:
            await ctx.send('Stopping...', delete_after=5)
            player.queue.clear()
            await player.stop()

    @commands.hybrid_command()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def remove(self, ctx, index: int):
        """Remove a specific song number from the queue."""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.queue:
            return await ctx.send("<:tickNo:697759586538749982> Nothing queued, use `play <song_name>`.", delete_after=5)
        if index > len(player.queue) or index < 1:
            return await ctx.send('<:tickNo:697759586538749982> Song number must be greater than 1 and within the queue limit.', delete_after=5)
        player.queue.pop(index-1)
        return await ctx.send('<:tickYes:697759553626046546> Removed from the queue.', delete_after=10)

    @commands.hybrid_command(aliases=['np', 'n', 'song'])
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def now(self, ctx):
        """Shows you the song currently playing."""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if player.is_playing:
            if player.current:
                if player.current.stream:
                    dur = 'LIVE'
                else:
                    dur = format_time(player.current.duration)
            e = discord.Embed(colour=discord.Color.blurple())
            e.title = "Now Playing:"
            e.description = f"{player.current.title}\n"
            e.description += f"{await self.draw_time(ctx.guild.id)} `[{format_time(player.position)}/{dur}]`\n"
            e.description += f"{player.current.uri}\n"
            e.set_thumbnail(url=f'https://img.youtube.com/vi/{player.current.identifier}/hqdefault.jpg')
            await ctx.send(embed=e, view=np_msg_buttons(self.bot, ctx.guild.id))
        else:
            if player.is_connected:
                return await ctx.send("<:tickNo:697759586538749982> Nothing is playing.", delete_after=5)

    @commands.hybrid_command(aliases=['forceskip', 'fs'])
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def skip(self, ctx, number: int=None):
        """Skips to the next track in the queue."""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if player.current is None:
            return await ctx.send("<:tickNo:697759586538749982> Nothing playing, use `play <song_name>`.", delete_after=5)
        if number is not None:
            results = await self.bot.lavalink.get_tracks(player.queue[number-1].uri)
            player.add(requester=ctx.author.id, track=results['tracks'][0])
            player.queue.insert(0, self.bot.lavalink.player_manager.get(ctx.guild.id).queue[len(player.queue) - 1])
            player.queue.pop(number)
            return await player.skip()
        else:
            return await player.skip()

    @commands.hybrid_command(aliases=['resume'])
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def pause(self, ctx):
        """Pauses or resumes music playback."""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.is_playing:
            return await ctx.send("<:tickNo:697759586538749982> Nothing playing, use `play <song_name>`.", delete_after=5)
        await player.set_pause(not player.paused)
        return await ctx.send("Done.", delete_after=5)

    @commands.hybrid_command(aliases=['q'], name="queue")
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def queue(self, ctx, page: int=1):
        """Shows you all the songs in queue."""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.queue:
            return await ctx.send('<:tickNo:697759586538749982> Nothing playing.', delete_after=4)
        if player.current.stream:
            dur = 'LIVE'
        else:
            dur = format_time(player.current.duration)
        pos = format_time(player.position)
        e = discord.Embed(colour=discord.Color.blurple())
        e.add_field(name="Currently Playing:", value=f"{player.current.title}\n{player.current.uri}\n{await self.draw_time(ctx.guild.id)} `[{pos}/{dur}]`")
        e.add_field(name="Up Next:", value=f"{await self.draw_queue(ctx.guild.id, page)}", inline=False)
        e.set_thumbnail(url=f'https://img.youtube.com/vi/{player.current.identifier}/hqdefault.jpg')
        if len(player.queue) > 10:
            e.set_footer(text=f'Page {page}/{math.ceil(len(player.queue) / 10)} | {len(player.queue)} tracks')
            return await ctx.send(embed=e, view=queue_msg_buttons(self.bot, ctx.guild.id, 1))
        else:
            return await ctx.send(embed=e)

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

    #All spotify request functions below
    async def queue_spotify(self, ctx, player, query):
        """Let's not make the play command look like fucking hell anymore....."""
        try:
            send = ctx.send
        except AttributeError:
            send = ctx.channel.send
        parts = query.split(":")
        if "track" in parts:
            res = await self.make_spotify_req("https://api.spotify.com/v1/tracks/{0}".format(parts[-1]))
            results = await player.node.get_tracks("ytsearch:{} {}".format(res["artists"][0]["name"], res["name"]))
            if results:
                track = AudioTrack(results['tracks'][0], ctx.author.id, recommended=True)
                player.add(requester=ctx.author.id, track=track)
            else:
                await ctx.send("<:tickNo:697759586538749982> Nothing was found!", delete_after=5)
        elif "album" in parts:
            loadingmsg = await send("<a:loading:697759686509985814> Loading spotify info...")
            query = parts[-1]
            results = await self.make_spotify_req("https://api.spotify.com/v1/albums/{0}".format(query))
            albumName = results['name']
            artistName = results['artists'][0]['name']
            if results:
                spotify_info = []
                while True:
                    try:
                        spotify_info.extend(results["tracks"]["items"])
                    except KeyError:
                        spotify_info.extend(results["items"])
                    try:
                        if results["next"] is not None:
                            results = await self.make_spotify_req(results["next"])
                            continue
                        else:
                            break
                    except KeyError:
                        if results["tracks"]["next"] is not None:
                            results = await self.make_spotify_req(results["tracks"]["next"])
                            continue
                        else:
                            break
                for i in spotify_info:
                    results = await player.node.get_tracks("ytsearch:{} {}".format(i["name"], i["artists"][0]["name"]))
                    track = AudioTrack(results['tracks'][0], ctx.author.id, recommended=True)
                    player.add(requester=ctx.author.id, track=track)
                await loadingmsg.delete()
                await send(f"<:tickYes:697759553626046546> Loaded Album **{albumName}** by **{artistName}!**", delete_after=5)
            else:
                await loadingmsg.delete()
                await send("<:tickNo:697759586538749982> Nothing was found!", delete_after=5)
        elif "playlist" in parts:
            loadingmsg = await send("<a:loading:697759686509985814> Loading spotify info...")
            query = parts[-1]
            results = await self.make_spotify_req("https://api.spotify.com/v1/playlists/{0}/tracks".format(query))
            playlistName = results['name']
            if results:
                spotify_info = []
                numberoftracks = 0
                while True:
                    try:
                        spotify_info.extend(results["tracks"]["items"])
                    except KeyError:
                        spotify_info.extend(results["items"])
                    try:
                        if results["next"] is not None:
                            results = await self.make_spotify_req(results["next"])
                            continue
                        else:
                            break
                    except KeyError:
                        if results["tracks"]["next"] is not None:
                            results = await self.make_spotify_req(results["tracks"]["next"])
                            continue
                        else:
                            break
                for i in spotify_info:
                    results = await player.node.get_tracks("ytsearch:{} {}".format(i["track"]["name"], i["track"]["artists"][0]["name"]))
                    track = AudioTrack(results['tracks'][0], ctx.author.id, recommended=True)
                    player.add(requester=ctx.author.id, track=track)
                await loadingmsg.delete()
                await send(f"<:tickYes:697759553626046546> Loaded Playlist **{playlistName}**!", delete_after=5)
            else:
                await loadingmsg.delete()
                await send("<:tickNo:697759586538749982> Nothing was found!", delete_after=5)
        player.store('channel', ctx.channel.id)
        if not player.is_playing:
            await player.play()

    async def make_spotify_req(self, url):
        if self.spotify_token and not self.spotify_token["expires_at"] - int(time.time()) < 60:
            token = self.spotify_token["access_token"]
        else:
            auth_header = base64.b64encode((self.bot.spotify_id + ":" + self.bot.spotify_secret).encode("ascii"))
            headers = {"Authorization": "Basic %s" % auth_header.decode("ascii")}
            slink = "https://accounts.spotify.com/api/token"
            async with self.bot.session.post(slink, data={"grant_type": "client_credentials"}, headers=headers) as r:
                if r.status != 200:
                    print(color(f"Issue making GET request to: [{url}] {r.status}{await r.json()}", fore=self.bot.colors["red"]))
                token = await r.json()
            if token is None:
                print(color("Requested a token from Spotify, did not end up getting one.", fore=self.bot.colors["red"]))
            token["expires_at"] = int(time.time()) + token["expires_in"]
            self.spotify_token = token
            token = self.spotify_token["access_token"]
            print(color("Created a new access token for Spotify!", fore=self.bot.colors["green"]))
        async with self.bot.session.request("GET", url, headers={"Authorization": "Bearer {0}".format(token)}) as r:
            if r.status != 200:
                print(color(f"Issue making GET request to: [{url}] {r.status}{await r.json()}", fore=self.bot.colors["red"]))
            return await r.json()

async def setup(bot):
    await bot.add_cog(Music(bot))