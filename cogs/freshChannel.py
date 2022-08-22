import re
import discord
import aiosqlite
import asyncio
from discord.ext import commands
from lavalink.models import AudioTrack
from lavalink.utils import format_time
from utils._LavalinkVoiceClient import LavalinkVoiceClient

class MusicChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        send = message.channel.send
        if message.guild:
            guildPrefix = await self.bot.prefix(message)
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
            if msg.startswith(guildPrefix):
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
                            await self.update_player_msg(player, playerMsg, "basic")
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
                        return await self.update_player_msg(player, playerMsg, "pause/resume")
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
                        await self.update_player_msg(player, playerMsg, "main")
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

    async def update_player_msg(self, player, playerMsg, status):
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
            return await playerMsg.edit(embed=e)
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
            if status == 'pause/resume':
                if player.paused == True:
                    e.title = "The music is currently paused"
                    e.add_field(name="Title:", value=player.current.title, inline=False)
                    e.set_image(url=f"https://img.youtube.com/vi/{player.current.identifier}/hqdefault.jpg")
                    requester = self.bot.get_user(player.current.requester)
                    e.set_footer(text=f"Requested by {requester.name}#{requester.discriminator}")
                else:
                    e.add_field(name="Currently Playing:", value=current, inline=False)
                    e.add_field(name="Author:", value=player.current.author)
                    e.add_field(name="Duration:", value=dur)
                    e.add_field(name="Queue List:", value=queue_list, inline=False)
                    e.set_image(url=f"https://img.youtube.com/vi/{player.current.identifier}/hqdefault.jpg")
                    requester = self.bot.get_user(player.current.requester)
                    e.set_footer(text=f"Requested by {requester.name}#{requester.discriminator}")
            elif status == "basic":
                e.add_field(name="Currently Playing:", value=current, inline=False)
                e.add_field(name="Author:", value=player.current.author)
                e.add_field(name="Duration:", value=dur)
                e.add_field(name="Queue List:", value=queue_list, inline=False)
                e.set_image(url=f'https://img.youtube.com/vi/{player.current.identifier}/hqdefault.jpg')
                requester = self.bot.get_user(player.current.requester)
                e.set_footer(text=f"Requested by {requester.name}#{requester.discriminator}")
            return await playerMsg.edit(embed=e)

    async def query_request(self, message, player, playerMsg, query: str.strip('<>')):
        if "open.spotify.com" in query:
            query = "{}".format(re.sub(r"(http[s]?:\/\/)?(open.spotify.com)\/", "", query).replace("/", ":"))
            await self.bot.get_cog('Music').queue_spotify(message, player, query)
            if player.queue:
                return await self.update_player_msg(player, playerMsg, 'basic')
        else:
            if not re.compile(r'https?://(?:www\.)?.+').match(query):
                query = f'ytsearch:{query}'
            results = await player.node.get_tracks(query)
            if not results or not results['tracks']:
                return await message.channel.send('Nothing found!', delete_after=5)
            if results['loadType'] == 'LOAD_FAILED':
                return await message.channel.send('Oh no, something failed. Please try again.', delete_after=5)
            if results['loadType'] == 'PLAYLIST_LOADED':
                for track in results['tracks']:
                    player.add(requester=message.author.id, track=track)
                if not player.is_playing:
                    await player.play()
                await self.update_player_msg(player, playerMsg, 'basic')
            else:
                track = AudioTrack(results['tracks'][0], message.author.id, recommended=True)
                player.add(requester=message.author.id, track=track)
                if not player.is_playing:
                    await player.play()
                if player.queue:
                    await self.update_player_msg(player, playerMsg, 'basic')

    async def create_search(self, message, player, playerMsg,  query):
        results = await self.bot.lavalink.get_tracks(f'ytsearch:{query}')
        if not results or not results['tracks']:
            return await message.channel.send('<:tickNo:697759586538749982> Nothing found!', delete_after=5)
        number = 0
        e = discord.Embed(colour=discord.Colour.blurple())
        e.description = ""
        for r in results['tracks']:
            number += 1
            e.description += f"**{number})** {r['info']['title']}\n"
        e.description += "\nPlease choose a result. Examples: `start 1` to play, `cancel` to cancel this search and delete messages."
        m = await message.channel.send(embed=e)
        def check(m):
            return m.channel == message.channel and m.author == message.author
        while True:
            try:
                msg = await self.bot.wait_for('message', check=check, timeout=60.0)
            except asyncio.TimeoutError:
                return await m.delete()
            if msg.content == 'cancel':
                return await m.delete()
            elif msg.content.startswith('start'):
                content = msg.content.replace('start ', '')
                if content.isdigit():
                    if int(content) > number:
                        await message.channel.send("<:tickNo:697759586538749982> Invalid number, try again.", delete_after=2)
                    else:
                        await m.delete()
                        e = discord.Embed(color=discord.Color.blurple())
                        track = results['tracks'][int(content)-1]
                        track = AudioTrack(track, message.author.id, recommended=True)
                        player.add(requester=message.author.id, track=track)
                        if not player.is_playing:
                            await player.play()
                        if player.queue:
                            return await self.update_player_msg(player, playerMsg, 'basic')
                        else:
                            return await message.channel.send(f"<:tickYes:697759553626046546> Added song {content} to queue.", delete_after=5)

async def setup(bot):
    await bot.add_cog(MusicChannel(bot))