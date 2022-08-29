import re
import discord
import aiosqlite
import asyncio
from aiohttp import request
from rich.console import Console
from discord.ext import commands
from lavalink.utils import format_time
from utils._LavalinkVoiceClient import LavalinkVoiceClient
from utils._MusicButtons import search_msg, event_hook

class MusicChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

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
                    if data is not None:
                        if data[1] == 1:
                            try:
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
                            except discord.errors.NotFound:
                                pass
                except Exception as e:
                    Console().print_exception(show_locals=False)

    @commands.Cog.listener()
    async def on_message(self, message):
        send = message.channel.send
        try:
            musicChannel, db, data = await self.check_channel(message)
        except:
            pass
        if message.author.bot or message.guild is None:
            return
        if musicChannel:
            if not re.compile(r'/https?:\/\/(?:www\.)?.+/gm').match(message.content):
                msg = message.content
            else:
                msg = message.content.lower()
            await message.delete()
            if msg.startswith("f?"):
                return
            try:
                inVoice = await self.check_voice(message)
            except:
                pass
            if inVoice:
                player = await self.create_player(message)  
            playerMsg = await message.channel.fetch_message(data[0])
            if not playerMsg:
                playerMsg = await self.create_player_msg(message, db, data)
            if msg.startswith('cancel') or msg.startswith('start'):
                return
            elif msg.startswith('search'):
                if inVoice:
                    self.bot.logger.info(f"Fresh Channel | Command search | Ran by {message.author.name} ({message.author.id}) in guild {message.guild.name}")
                    return await self.create_search(message, player, playerMsg, msg.replace('search', ''))
            elif msg.startswith('rem') or msg.startswith('remove'):
                if inVoice:
                    self.bot.logger.info(f"Fresh Channel | Command remove | Ran by {message.author.name} ({message.author.id}) in guild {message.guild.name}")
                    index = msg.replace('rem', '').replace('ove', '').replace(' ', '')
                    if index.isdigit():
                        if player.queue:
                            if int(index) > len(player.queue) or int(index) < 1:
                                return await send('<:tickNo:697759586538749982> Song number must be greater than 1 and within the queue limit.', delete_after=5)
                            player.queue.pop(int(index)-1)
                            await self.update_player_msg(player, message.guild, playerMsg, "basic")
                            return await send(f"<:tickYes:697759553626046546> Removed song {index} from the queue.", delete_after=5)
                    else:
                        return await send("<:tickNo:697759586538749982> Index must be 1 or inside the queue index.", delete_after=5)
            elif msg.startswith('vol') or msg.startswith('volume'):
                if inVoice:
                    self.bot.logger.info(f"Fresh Channel | Command volume | Ran by {message.author.name} ({message.author.id}) in guild {message.guild.name}")
                    volume = msg.replace('vol').replace('ume').replace(' ', '')
                    if volume == "":
                        return await message.channel.send(f'🔈 | {player.volume}%', delete_after=5)
                    if volume.isdigit():
                        volume = int(volume)
                        if volume > 100:
                            volume = 100
                        await player.set_volume(volume)
                        return await message.channel.send(f'🔈 | Set to {player.volume}%', delete_after=5)
                    else:
                        return await send("<:tickNo:697759586538749982> Volume must be a number.", delete_after=5)
            elif msg.startswith('pause') or msg.startswith('resume'):
                if inVoice:
                    self.bot.logger.info(f"Fresh Channel | Command pause/resume | Ran by {message.author.name} ({message.author.id}) in guild {message.guild.name}")
                    if player.is_playing:
                        await player.set_pause(not player.paused)
                        return await self.update_player_msg(player, message.guild, playerMsg, "pause/resume")
            elif msg.startswith('skip'):
                if inVoice:
                    self.bot.logger.info(f"Fresh Channel | Command skip | Ran by {message.author.name} ({message.author.id}) in guild {message.guild.name}")
                    if player.is_playing:
                        return await player.skip()
            elif msg.startswith('dc') or msg.startswith('disconnect'):
                if inVoice:
                    self.bot.logger.info(f"Fresh Channel | Command disconnect | Ran by {message.author.name} ({message.author.id}) in guild {message.guild.name}")
                    if inVoice:
                        await message.guild.voice_client.disconnect(force=True)
                        await self.update_player_msg(player, message.guild, playerMsg, "main")
                        return self.bot.lavalink.player_manager.remove(message.guild.id)
            elif msg.startswith('help'):
                e = discord.Embed(color=discord.Color.blurple())
                e.description = "Send a song `link` or `query` to play."
                e.description += "\nSend `pause` or `resume` to control the music."
                e.description += "\nSend `skip` to skip the current song."
                e.description += "\nSend `prev` or `previous` to skip to the previous song."
                e.description += "\nSend `dc` or `disconnect` to disconnect from the voice channel."
                e.description += "\nSend `vol 10` or `volume 10` to change the volume."
                e.description += "\nSend `rem 1` or `remove 1` to remove a song from the queue."
                e.description += "\nSend `search <query>` to search for a song."
                e.description += "\nSend `stop` to stop the player."
                e.set_footer(text="This message will delete in 30 seconds.")
                return await send(embed=e, delete_after=30)
            else:
                if inVoice:
                    return await self.query_request(message, player, playerMsg, msg)

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
                    channelid = [e.id for e in ctx.guild.channels if e.name == 'fresh-music'][0]
                    channel = await ctx.guild.fetch_channel(channelid)
                    await channel.delete()
                created = await ctx.guild.create_text_channel(name="fresh-music", topic="THIS IS IN BETA, PLEASE REPORT BUGS TO Jonny#0181")
                msgid = await self.create_initial_player_message(created.id)
                await db.execute("INSERT INTO musicSettings (musicMessage, musicToggle, musicChannel, musicRunning, guild) VALUES (?, ?, ?, ?, ?)", (msgid, 1, created.id, 0, ctx.guild.id,))
            elif data[0] == 1:
                if "fresh-music" in existing_channels:
                    channel = await ctx.guild.fetch_channel(data[1])
                    await channel.delete()
                await db.execute("UPDATE musicSettings SET musicToggle = ? WHERE guild = ?", (0, ctx.guild.id,))
                await ctx.send("<:tickYes:697759553626046546> Disabled the music channel.")
            else:
                if "fresh-music" in existing_channels:
                    channelid = [e.id for e in ctx.guild.channels if e.name == 'fresh-music'][0]
                    channel = await ctx.guild.fetch_channel(channelid)
                    await channel.delete()
                created = await ctx.guild.create_text_channel(name="fresh-music", topic="THIS IS IN BETA, PLEASE REPORT BUGS TO Jonny#0181")
                msgid = await self.create_initial_player_message(created.id)
                await db.execute("UPDATE musicSettings SET musicMessage = ?, musicToggle = ?, musicChannel = ? WHERE guild = ?", (msgid, 1, created.id, ctx.guild.id,))
                await ctx.send(f"<:tickYes:697759553626046546> Music channel setup complete. You can now move <#{created.id}> to wherever you want.")
            await db.commit()
            
    async def create_initial_player_message(self, channelid):
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

    async def check_channel(self, message):
        if message.guild:
            async with aiosqlite.connect("./data/music.db") as db:
                getData = await db.execute("SELECT musicMessage, musicToggle, musicChannel, musicRunning FROM musicSettings WHERE guild = ?", (message.guild.id,))
                data = await getData.fetchone()
                if not data:
                    return
                if data[1] == 1:
                    if message.channel.id == data[2]:
                        return True, db, data
                    else:
                        return False, db, data
        else:
            return False, None, None

    async def create_player(self, message):
        inVoice = await self.check_voice(message)
        if inVoice:
            player = self.bot.lavalink.player_manager.create(message.guild.id, endpoint="us")
            if player.channel_id is not None:
                if int(player.channel_id) != message.author.voice.channel.id:
                    await message.channel.send('<:tickNo:697759586538749982> You need to be in my voicechannel.', delete_after=5)
                    return False
            if not player.is_connected:
                player.store('channel', message.channel.id)
                await message.author.voice.channel.connect(cls=LavalinkVoiceClient)
            return player

    async def check_voice(self, message):
        if not message.author.voice or not message.author.voice.channel:
            await message.channel.send('<:tickNo:697759586538749982> Join a voicechannel first.', delete_after=5)
            return False
        if not message.author.voice.channel.permissions_for(message.guild.me).connect or not message.author.voice.channel.permissions_for(message.guild.me).speak:
            await message.channel.send('<:tickNo:697759586538749982> I need the `CONNECT` and `SPEAK` permissions.', delete_after=5)
            return False
        return True

    async def create_player_msg(self, message, db, data):
        e = discord.Embed(color=discord.Color.blurple())
        e.title = "Nothing Currently Playing:"
        e.description = "Send a song `link` or `query` to play."
        e.description += "\nSend `pause` or `resume` to control the music."
        e.description += "\nSend `skip` to skip the current song."
        e.description += "\nSend `dc` or `disconnect` to disconnect from the voice channel."
        e.description += "\nSend `vol 10` or `volume 10` to change the volume."
        e.description += "\nSend `rem 1` or `remove 1` to remove a song from the queue."
        e.description += "\nSend `search <query>` to search for a song."
        e.description += "\nSend `stop` to stop the player."
        e.set_image(url="https://i.imgur.com/VIYaATs.jpg")
        msg = await self.bot.get_channel(data[2]).send(embed=e)
        await db.execute("UPDATE musicSettings SET musicMessage = ? WHERE guild = ?", (msg.id, message.guild.id,))
        await db.commit()
        return await message.channel.fetch_message(msg.id)

    async def update_player_msg(self, player, guild, playerMsg, status):
        if status == "main":
            e = discord.Embed(color=discord.Colour.blurple())
            e.title = "Nothing Currently Playing:"
            e.description = "Send a song `link` or `query` to play."
            e.description += "\nSend `pause` or `resume` to control the music."
            e.description += "\nSend `skip` to skip the current song."
            e.description += "\nSend `dc` or `disconnect` to disconnect from the voice channel."
            e.description += "\nSend `vol 10` or `volume 10` to change the volume."
            e.description += "\nSend `rem 1` or `remove 1` to remove a song from the queue."
            e.description += "\nSend `search <query>` to search for a song."
            e.description += "\nSend `stop` to stop the player."
            e.set_image(url="https://i.imgur.com/VIYaATs.jpg")
            await playerMsg.edit(embed=e, view=event_hook(self.bot, guild.id))
        else:
            if player.queue:
                queue_list = ''
                for i, track in enumerate(player.queue[(1 - 1) * 5:(1 - 1) * 5 + 5], start=(1 - 1) * 5):
                    queue_list += '`{}.` {}\n'.format(i + 1, track.title)
            else:
                queue_list = "Join a voice channel and queue songs by name or url in here."
            if player.current.stream:
                dur = 'LIVE'
            else:
                dur = format_time(player.current.duration)
            current = f"{player.current.title}\n{player.current.uri}"
            e = discord.Embed(color=discord.Colour.blurple())
            if "open.spotify.com" in str(player.current.uri):
                url = f"https://open.spotify.com/oembed?url={player.current.uri}"
                async with request("GET", url) as response:
                    json = await response.json()
                    e.set_image(url=f"{json['thumbnail_url']}")
            else:
                e.set_image(url=f"https://img.youtube.com/vi/{player.current.identifier}/hqdefault.jpg")
            if status == 'pause/resume':
                if player.paused == True:
                    e.title = "The music is currently paused"
                    e.add_field(name="Title:", value=player.current.title, inline=False)
                    requester = self.bot.get_user(player.current.requester)
                    e.set_footer(text=f"Requested by {requester.name}#{requester.discriminator}")
                else:
                    e.add_field(name="Currently Playing:", value=current, inline=False)
                    e.add_field(name="Author:", value=player.current.author)
                    e.add_field(name="Duration:", value=dur)
                    e.add_field(name="Queue List:", value=queue_list, inline=False)
                    requester = self.bot.get_user(player.current.requester)
                    e.set_footer(text=f"Requested by {requester.name}#{requester.discriminator}")
            elif status == "basic":
                e.add_field(name="Currently Playing:", value=current, inline=False)
                e.add_field(name="Author:", value=player.current.author)
                e.add_field(name="Duration:", value=dur)
                e.add_field(name="Queue List:", value=queue_list, inline=False)
                requester = self.bot.get_user(player.current.requester)
                e.set_footer(text=f"Requested by {requester.name}#{requester.discriminator}")
            await playerMsg.edit(embed=e, view=event_hook(self.bot, guild.id))

    async def query_request(self, message, player, playerMsg, query: str.strip('<>')):
        player = self.bot.lavalink.player_manager.players.get(message.guild.id)
        query = query.strip('<>')
        e = discord.Embed(color=discord.Color.blurple())
        if not re.compile(r'https?:\/\/(?:www\.)?.+').match(query) and not query.startswith('spotify:'):
            query = f'spsearch:{query}'
        results = await self.bot.lavalink.get_tracks(query, check_local=True)
        if not results or not results.tracks:
            return await message.channel.send('Nothing found!', delete_after=5)
        if results.load_type == 'PLAYLIST_LOADED':
            tracks = results.tracks
            for track in tracks:
                player.add(requester=message.author.id, track=track)
            e.title = "Playlist Enqueued!"
            e.description = f"{results.playlist_info.name} with {len(tracks)} tracks."
            await message.channel.send(embed=e, delete_after=5)
        else:
            track = results.tracks[0]
            player.add(requester=message.author.id, track=track)
            if player.queue:
                e.title = "Track Enqueued!"
                e.description = f"{track.title}\n{track.uri}"
                await message.channel.send(embed=e, delete_after=5)
        if not player.is_playing:
            player.store('channel', message.channel.id)
            await player.play()
        await self.update_player_msg(player, message.guild, playerMsg, 'basic')

    async def create_search(self, message, player, playerMsg, query):
        results = await self.bot.lavalink.get_tracks(f'ytsearch:{query}')
        if not results or not results['tracks']:
            return await message.channel.send('<:tickNo:697759586538749982> Nothing found!', delete_after=5)
        else:
            e = discord.Embed(color=discord.Color.blurple())
            e.title = 'Search Results'
            e.description = f'{results["tracks"][0]["info"]["title"]}\n{results["tracks"][0]["info"]["uri"]}'
            e.add_field(name="Author", value=results["tracks"][0]["info"]["author"])
            e.add_field(name="Duration", value=format_time(results["tracks"][0]["info"]["duration"]))
            picID = results["tracks"][0]["info"]["identifier"]
            e.set_thumbnail(url=f"https://img.youtube.com/vi/{picID}/hqdefault.jpg")
            await message.channel.send(embed=e, view=search_msg(self.bot, message.guild.id, results))

async def setup(bot):
    await bot.add_cog(MusicChannel(bot))