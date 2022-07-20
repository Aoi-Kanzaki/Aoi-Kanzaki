import base64
import time
import re
import math
import asyncio
import discord
import lavalink
from colr import color
from lavalink.utils import format_time
from lavalink.models import AudioTrack
from discord.ext import commands

class LavalinkVoiceClient(discord.VoiceClient):

    def __init__(self, client: discord.Client, channel: discord.abc.Connectable):
        self.client = client
        self.channel = channel
        # ensure there exists a client already
        if hasattr(self.client, 'lavalink'):
            self.lavalink = self.client.lavalink
        else:
            self.client.lavalink = lavalink.Client(client.user.id)
            self.client.lavalink.add_node( 'localhost', 2333, 'youshallnotpass', 'us', 'default-node')
            self.lavalink = self.client.lavalink

    async def on_voice_server_update(self, data):
        await self.lavalink.voice_update_handler({ 't': 'VOICE_SERVER_UPDATE', 'd': data })

    async def on_voice_state_update(self, data):
        await self.lavalink.voice_update_handler({ 't': 'VOICE_STATE_UPDATE', 'd': data })

    async def connect(self, *, timeout: float, reconnect: bool, self_deaf: bool = False, self_mute: bool = False) -> None:
        self.lavalink.player_manager.create(guild_id=self.channel.guild.id)
        await self.channel.guild.change_voice_state(channel=self.channel, self_mute=self_mute, self_deaf=self_deaf)

    async def disconnect(self, *, force: bool = False) -> None:
        player = self.lavalink.player_manager.get(self.channel.guild.id)
        if not force and not player.is_connected:
            return
        await self.channel.guild.change_voice_state(channel=None)
        player.channel_id = None
        player.store("prev_requester", None)
        player.store("prev_song", None)
        player.store("playing_song", None)
        player.store("requester", None)
        self.cleanup()

class np_msg_buttons(discord.ui.View):
    def __init__(self, bot, guild_id) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id
        self.player = bot.lavalink.player_manager.get(self.guild_id)

    @discord.ui.button(label="Queue", style=discord.ButtonStyle.blurple)
    async def queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not self.player.queue:
            return await interaction.response.send_message(content="Nothing playing.", ephemeral=True)
        if self.player.current.stream:
            dur = 'LIVE'
        else:
            dur = format_time(self.player.current.duration)
        pos = format_time(self.player.position)
        e = discord.Embed(colour=discord.Color.blurple())
        draw_time = await self.bot.get_cog("Music").draw_time(self.guild_id)
        draw_queue = await self.bot.get_cog("Music").draw_queue(self.guild_id, 1)
        e.add_field(name="Currently Playing:", value=f"{self.player.current.title}\n{self.player.current.uri}\n{draw_time} `[{pos}/{dur}]`")
        e.add_field(name="Up Next:", value=f"{draw_queue}", inline=False)
        if len(self.player.queue) > 10:
            e.set_footer(text=f'Not showing {len(self.player.queue)-10} tracks')
        return await interaction.response.edit_message(embed=e)

    @discord.ui.button(label="Pause/Resume", style=discord.ButtonStyle.blurple)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_pause(not self.player.paused)
        e = discord.Embed(colour=discord.Color.blurple())
        if self.player.current.stream:
            dur = 'LIVE'
        else:
            dur = format_time(self.player.current.duration)
        if self.player.paused is True:
            e.title = "Paused:"
        else:
            e.title = "Now Playing:"
        draw_time = await self.bot.get_cog("Music").draw_time(self.guild_id)
        e.description = f"{self.player.current.title}\n"
        e.description += f"{draw_time} `[{format_time(self.player.position)}/{dur}]`\n"
        e.description += f"{self.player.current.uri}\n"
        e.set_thumbnail(url=f'https://img.youtube.com/vi/{self.player.current.identifier}/hqdefault.jpg')
        return await interaction.response.edit_message(embed=e)

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.blurple)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.skip()
        return await interaction.response.send_message(content="✅ Skipped.", ephemeral=True)

    @discord.ui.button(label="Quit", style=discord.ButtonStyle.red)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.player.queue.clear()
        await self.player.stop()
        return await interaction.response.send_message(content="⏹️ Stopped music and cleared queue.", ephemeral=True)

class event_hook_buttons(discord.ui.View):
    def __init__(self, bot, guild_id) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.player = bot.lavalink.player_manager.get(guild_id)

    @discord.ui.button(label="Previous", style=discord.ButtonStyle.blurple)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.player.fetch("prev_song") is None:
            return await interaction.response.send_message(content="No previous track.", ephemeral=True)
        last_track = await self.player.node.get_tracks(self.player.fetch("prev_song"))
        if not last_track:
            return interaction.response.edit_message(content="Seems there was an issue in getting the last track and nothing was found.", embed=None, view=None)
        self.player.add(requester=self.player.fetch("prev_requester"), track=last_track['tracks'][0])
        self.player.queue.insert(0, self.player.queue[-1])
        self.player.queue.pop(len(self.player.queue)-1)
        await self.player.skip()
        self.player.store("prev_requester", None)
        self.player.store("prev_song", None)
        self.player.store("playing_song", None)
        self.player.store("requester", None)
        embed = discord.Embed(colour=discord.Color.blurple(), title="Replaying Track", description=f"**[{self.player.current.title}]({self.player.current.uri})**")
        return await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Pause/Resume", style=discord.ButtonStyle.blurple)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_pause(not self.player.paused)
        e = discord.Embed(colour=discord.Color.blurple())
        if self.player.paused is True:
            e.title = "Paused:"
        else:
            e.title = "Now Playing:"
        e.description = f"{self.player.current.title}\n"
        e.description += f"{self.player.current.uri}\n"
        e.set_thumbnail(url=f'https://img.youtube.com/vi/{self.player.current.identifier}/hqdefault.jpg')
        if self.player.queue:
            number = 0
            upNext = ""
            for track in self.player.queue[0:5]:
                number += 1
                upNext += f"`{number})` {track.title}\n"
            e.add_field(name="Up Next:", value=upNext)
        return await interaction.response.edit_message(embed=e)

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.blurple)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.skip()
        return await interaction.response.send_message(content="✅ Skipped.", ephemeral=True)

    @discord.ui.button(label="Quit", style=discord.ButtonStyle.red)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.player.queue.clear()
        await self.player.stop()
        return await interaction.response.send_message(content="⏹️ Stopped music and cleared queue.", ephemeral=True)

class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.spotify_token = None
        if not hasattr(bot, 'lavalink'):
            bot.lavalink = lavalink.Client(bot.user.id)
            bot.lavalink.add_node(host='127.0.0.1', port=2333, password='youshallnotpass', region='eu', name='default-node', resume_timeout=None, reconnect_attempts=3)
        lavalink.add_event_hook(self.track_hook)

    def cog_unload(self):
        self.bot.lavalink._event_hooks.clear()

    async def cog_before_invoke(self, ctx):
        if ctx.guild is not None:
            await self.ensure_voice(ctx)
        return ctx.guild is not None

    async def cog_command_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            print(color(f"Error in command {ctx.command.name}\n{error}", fore=self.bot.colors["red"]))

    async def ensure_voice(self, ctx):
        player = self.bot.lavalink.player_manager.create(ctx.guild.id, endpoint="us")
        if not ctx.author.voice or not ctx.author.voice.channel:
            return await ctx.send('<:tickNo:697759586538749982> Join a voicechannel first.')
        if not player.is_connected:
            if not ctx.command.name in ('play', 'search'):
                return await ctx.send('<:tickNo:697759586538749982> Not connected.')
            if not ctx.author.voice.channel.permissions_for(ctx.me).connect or not ctx.author.voice.channel.permissions_for(ctx.me).speak:
                return await ctx.send('<:tickNo:697759586538749982> I need the `CONNECT` and `SPEAK` permissions.')
            player.store('channel', ctx.channel.id)
            await ctx.author.voice.channel.connect(cls=LavalinkVoiceClient)
        else:
            if int(player.channel_id) != ctx.author.voice.channel.id:
                return await ctx.send('<:tickNo:697759586538749982> You need to be in my voicechannel.')

    async def track_hook(self, event):
        if not hasattr(event, 'player'):
            return
        if isinstance(event, lavalink.events.NodeConnectedEvent):
            print(color(f"Lavalink succesfully connected to node:", fore=self.bot.colors['cyan']), color(f"{event.node.name}", fore=self.bot.colors['purple']))
        if isinstance(event, lavalink.events.QueueEndEvent):
            return await self.bot.get_guild(int(event.player.guild_id)).voice_client.disconnect(force=True)
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

    @commands.hybrid_command(aliases=['p'])
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def play(self, ctx, *, query: str):
        """ Searches and plays a song from a given query. """
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        query = query.strip('<>')
        if "open.spotify.com" in query:
            query = "{}".format(re.sub(r"(http[s]?:\/\/)?(open.spotify.com)\/", "", query).replace("/", ":"))
            return await self.queue_spotify(ctx, player, query)
        if not re.compile(r'https?://(?:www\.)?.+').match(query):
            query = f'ytsearch:{query}'
        results = await player.node.get_tracks(query)
        if not results or not results['tracks']:
            return await ctx.send('Nothing found!')
        embed = discord.Embed(color=discord.Color.blurple())
        if results['loadType'] == 'LOAD_FAILED':
            await ctx.voice_client.disconnect(force=True)
            self.bot.lavalink.player_manager.remove(ctx.guild.id)
            return await ctx.send('Oh no, something failed. Please try again.')
        if results['loadType'] == 'PLAYLIST_LOADED':
            tracks = results['tracks']
            for track in tracks:
                player.add(requester=ctx.author.id, track=track)
            embed.title = 'Playlist Enqueued!'
            embed.description = f'{results["playlistInfo"]["name"]} - {len(tracks)} tracks'
        else:
            track = results['tracks'][0]
            embed.title = 'Track Enqueued'
            embed.description = f'[{track["info"]["title"]}]({track["info"]["uri"]})'
            await ctx.send(embed=embed, delete_after=5)
            track = AudioTrack(track, ctx.author.id, recommended=True)
            player.add(requester=ctx.author.id, track=track)
        if not player.is_playing:
            await player.play()

    @commands.hybrid_command(aliases=["prev"])
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def previous(self, ctx):
        """Returns to the previous song that played."""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if player.fetch("prev_song") is None:
            return await ctx.send("<:tickNo:697759586538749982> No previous track.")
        last_track = await player.node.get_tracks(player.fetch("prev_song"))
        if not last_track:
            return await ctx.send("<:tickNo:697759586538749982> Seems there was an issue in getting the last track and nothing was found.")
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
            return await ctx.send(f'🔈 | {player.volume}%')
        if volume > 100:
            volume = 100
        await player.set_volume(volume)
        return await ctx.send(f'🔈 | Set to {player.volume}%')

    @commands.hybrid_command()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def search(self, ctx, query):
        """Search for something to play."""
        results = await self.bot.lavalink.get_tracks(f'ytsearch:{query}')
        if not results or not results['tracks']:
            return await ctx.send('<:tickNo:697759586538749982> Nothing found!')
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
            await ctx.send('<:tickNo:697759586538749982> Nothing queued.')
        if number > len(player.queue) or number < 1:
            await ctx.send('<:tickNo:697759586538749982> Song number must be greater than 1 and within the queue limit.')
        player.queue.insert(0, self.bot.lavalink.player_manager.get(ctx.guild.id).queue[number-1])
        player.queue.pop(number)
        return await ctx.send('<:tickYes:697759553626046546> Moved to the top of the queue.', delete_after=10)

    @commands.hybrid_command()
    async def clear(self, ctx):
        """Clears the queue, doesn't stop the player tho."""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.queue:
            await ctx.send("<:tickNo:697759586538749982> Nothing queued, use `play <song_name>`.")
            return
        else:
            player.queue.clear()
            return await ctx.send("<:tickYes:697759553626046546> Cleared queue.", delete_after=10)

    @commands.hybrid_command()
    async def stop(self, ctx):
        """Stops playback of the song and clears the queue."""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if player.is_playing:
            await ctx.send('Stopping...')
            player.queue.clear()
            await player.stop()

    @commands.hybrid_command()
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def remove(self, ctx, index: int):
        """Remove a specific song number from the queue."""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if not player.queue:
            return await ctx.send("<:tickNo:697759586538749982> Nothing queued, use `play <song_name>`.")
        if index > len(player.queue) or index < 1:
            return await ctx.send('<:tickNo:697759586538749982> Song number must be greater than 1 and within the queue limit.')
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
                return await ctx.send("<:tickNo:697759586538749982> Nothing is playing.")

    @commands.hybrid_command(aliases=['forceskip', 'fs'])
    @commands.cooldown(1, 5, commands.BucketType.guild)
    async def skip(self, ctx, number: int=None):
        """Skips to the next track in the queue."""
        player = self.bot.lavalink.player_manager.get(ctx.guild.id)
        if player.current is None:
            return await ctx.send("<:tickNo:697759586538749982> Nothing playing, use `play <song_name>`.")
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
            return await ctx.send("<:tickNo:697759586538749982> Nothing playing, use `play <song_name>`.")
        await player.set_pause(not player.paused)
        return await ctx.message.add_reaction('\u2705')

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
        e.set_footer(text=f'Page {page}/{math.ceil(len(player.queue) / 10)} | {len(player.queue)} tracks')
        msg = await ctx.send(embed=e)
        def check(r, u):
            return r.message.id == msg.id and u == ctx.author
        for i in ['❌', '◀', '▶', '🔢']:
            await msg.add_reaction(i)
        while True:
            try:
                (reaction, user) = await self.bot.wait_for('reaction_add', check=check, timeout=60.0)
            except asyncio.TimeoutError:
                return
            if str(reaction.emoji) == "❌":
                await msg.delete()
            elif str(reaction.emoji) == "◀":
                await msg.remove_reaction('◀', ctx.author)
                page = page-1
                if page < 1:
                    page = math.ceil(len(player.queue) / 10)
                pos = format_time(player.position)
                if player.current.stream:
                    dur = 'LIVE'
                else:
                    dur = format_time(player.current.duration)
                e = discord.Embed(colour=discord.Color.blurple())
                e.add_field(name="Currently Playing:", value=f"{player.current.title}\n{player.current.uri}\n{await self.draw_time(ctx.guild.id)} `[{pos}/{dur}]`")
                e.add_field(name="Up Next:", value=f"{await self.draw_queue(ctx.guild.id, page)}", inline=False)
                e.set_footer(text=f'Page {page}/{math.ceil(len(player.queue) / 10)} | {len(player.queue)} tracks')
                await msg.edit(embed=e)
            elif str(reaction.emoji) == "▶":
                await msg.remove_reaction('▶', ctx.author)
                page = page+1
                if page > math.ceil(len(player.queue) / 10):
                    page = 1
                pos = format_time(player.position)
                if player.current.stream:
                    dur = 'LIVE'
                else:
                    dur = format_time(player.current.duration)
                e = discord.Embed(colour=discord.Color.blurple())
                e.add_field(name="Currently Playing:", value=f"{player.current.title}\n{player.current.uri}\n{await self.draw_time(ctx.guild.id)} `[{pos}/{dur}]`")
                e.add_field(name="Up Next:", value=f"{await self.draw_queue(ctx.guild.id, page)}", inline=False)
                text = 'Page {}/{} | {} tracks'.format(page, math.ceil(len(player.queue) / 10), len(player.queue))
                e.set_footer(text=f'Page {page}/{math.ceil(len(player.queue) / 10)} | {len(player.queue)} tracks')
                await msg.edit(embed=e)
            elif str(reaction.emoji) == "🔢":
                m = await ctx.send('What page would you like to go to?')
                def a(m):
                    return m.channel == ctx.channel and m.author == ctx.author
                while True:
                    try:
                        e = await ctx.bot.wait_for('message', check=a, timeout=60.0)
                    except asyncio.TimeoutError:
                        return
                    if e.content.isdigit():
                        if int(e.content) > math.ceil(len(player.queue) / 10):
                            await ctx.send('<:tickNo:697759586538749982> Invalid page. Try again.', delete_after=4)
                        elif int(e.content) < 1:
                            await ctx.send('<:tickNo:697759586538749982> Invalid page. Try again.', delete_after=4)
                        else:
                            await msg.delete()
                            await m.delete()
                            await ctx.invoke(self.bot.get_command('queue'), page=int(e.content))
                            return

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
        msg = await ctx.send("<a:loading:697759686509985814> Loading Spotify info...")
        parts = query.split(":")
        if "track" in parts:
            res = await self.make_spotify_req("https://api.spotify.com/v1/tracks/{0}".format(parts[-1]))
            results = await player.node.get_tracks("ytsearch:{} {}".format(res["artists"][0]["name"], res["name"]))
            if results:
                enqueuemsg = f'<:tickYes:697759553626046546> Track Enqueued: {results["tracks"][0]["info"]["title"]}'
                track = AudioTrack(results['tracks'][0], ctx.author.id, recommended=True)
                player.add(requester=ctx.author.id, track=track)
            else:
                enqueuemsg = "<:tickNo:697759586538749982> Nothing was found!"
        elif "album" in parts:
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
                enqueuemsg = f"<:tickYes:697759553626046546> Loaded Album **{albumName}** by **{artistName}!**"
            else:
                enqueuemsg = "<:tickNo:697759586538749982> Nothing was found!"
        elif "playlist" in parts:
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
                            continuez
                        else:
                            break
                for i in spotify_info:
                    results = await player.node.get_tracks("ytsearch:{} {}".format(i["track"]["name"], i["track"]["artists"][0]["name"]))
                    track = AudioTrack(results['tracks'][0], ctx.author.id, recommended=True)
                    player.add(requester=ctx.author.id, track=track)
                enqueuemsg = f"<:tickYes:697759553626046546> Loaded playlist **{playlistName}!**"
            else:
                enqueuemsg = "<:tickNo:697759586538749982> Nothing was found!"
        player.store('channel', ctx.channel.id)
        if not player.is_playing:
            await player.play()
        msg =  await msg.edit(content=enqueuemsg)
        await asyncio.sleep(10)
        return await msg.delete()

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