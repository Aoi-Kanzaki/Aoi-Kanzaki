import re
import discord
import asyncio
from aiohttp import request
from rich.console import Console
from discord.ext import commands
from lavalink.utils import format_time
from utils._LavalinkVoiceClient import LavalinkVoiceClient
from utils._MusicButtons import search_msg, event_hook, favorites

class MusicChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        fresh = bot.tree
        self.db = self.bot.db.fresh_channel
        self.bot.add_view(favorites(self.bot))

        @fresh.command(name="setup")
        async def setup(interaction: discord.Interaction):
            """Enables or disables the music channel in your guild."""
            existing_channels = [e.name for e in interaction.guild.channels]
            data = self.db.find_one({"_id": interaction.guild.id})
            if data is None:
                if "fresh-music" in existing_channels:
                    channelid = [e.id for e in interaction.guild.channels if e.name == 'fresh-music'][0]
                    channel = await interaction.guild.fetch_channel(channelid)
                    await channel.delete()
                created = await interaction.guild.create_text_channel(
                    name="fresh-music", topic="THIS IS IN BETA, PLEASE REPORT BUGS TO Jonny#0181")
                msgid = await self.create_initial_player_message(created.id, interaction.guild)
                self.db.insert_one({"_id": interaction.guild.id, "message": msgid, "channel": created.id, "toggle": True})
                return await interaction.response.send_message(
                        f"<:tickYes:697759553626046546> Music channel setup complete. You can now move <#{created.id}> to wherever you want.")
            else:
                if data['toggle'] is True:
                    if "fresh-music" in existing_channels:
                        channel = await interaction.guild.fetch_channel(data['channel'])
                        await channel.delete()
                    data['toggle'] = False
                    self.db.update_one({"_id": interaction.guild.id}, {"$set": data})
                    return await interaction.response.send_message(
                        "<:tickYes:697759553626046546> Disabled the music channel.")
                else:
                    if "fresh-music" in existing_channels:
                        channelid = [e.id for e in interaction.guild.channels if e.name == 'fresh-music'][0]
                        channel = await interaction.guild.fetch_channel(channelid)
                        await channel.delete()
                    created = await interaction.guild.create_text_channel(
                        name="fresh-music", topic="THIS IS IN BETA, PLEASE REPORT BUGS TO Jonny#0181")
                    msgid = await self.create_initial_player_message(created.id, interaction.guild)
                    self.db.update_one({"_id": interaction.guild.id}, {"$set": {"toggle": True, "message": msgid, "channel": created.id}})
                    return await interaction.response.send_message(
                        f"<:tickYes:697759553626046546> Music channel setup complete. You can now move <#{created.id}> to wherever you want.")

    async def cog_unload(self):
        self.bot.lavalink._event_hooks.clear()
        for guild in self.bot.guilds:
            try:
                data = self.db.find_one({"_id": guild.id})
                if data != None:
                    if data['toggle'] is True:
                        channel = await guild.fetch_channel(data['channel'])
                        msg = await channel.fetch_message(data['message'])
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
                        await msg.edit(embed=e, view=favorites(self.bot))
                        await asyncio.sleep(1)
            except Exception as e:
                Console().print_exception(show_locals=False)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.guild is None: return
        if message.content.startswith("f?"): return
        data = self.db.find_one({"_id": message.guild.id})
        if data is not None:
            if message.channel.id == data['channel']:
                if not re.compile(r'/https?:\/\/(?:www\.)?.+/gm').match(message.content):
                    msg = message.content
                else:
                    msg = message.content.lower()
                await message.delete()
                inVoice = await self.check_voice(message)
                if inVoice:
                    player = await self.create_player(message)
                try:
                    playerMsg = await message.channel.fetch_message(data['message'])
                except discord.errors.NotFound:
                    playerMsg = await self.create_player_msg(message)
                if msg.startswith('cancel') or msg.startswith('start'): return
                elif msg.startswith('search'):
                    if inVoice:
                        self.bot.logger.info(
                            f"Fresh Channel | Command search | Ran by {message.author.name} ({message.author.id}) in guild {message.guild.name}")
                        return await self.create_search(message, msg.replace('search', ''))
                elif msg.startswith('rem') or msg.startswith('remove'):
                    if inVoice:
                        self.bot.logger.info(
                            f"Fresh Channel | Command remove | Ran by {message.author.name} ({message.author.id}) in guild {message.guild.name}")
                        index = msg.replace('rem', '').replace('ove', '').replace(' ', '')
                        if index.isdigit():
                            if player.queue:
                                if int(index) > len(player.queue) or int(index) < 1:
                                    return await message.channel.send(
                                        '<:tickNo:697759586538749982> Song number must be greater than 1 and within the queue limit.', delete_after=5)
                                player.queue.pop(int(index)-1)
                                await self.update_player_msg(player, message.guild, playerMsg, "basic")
                                return await message.channel.send(
                                    f"<:tickYes:697759553626046546> Removed song {index} from the queue.", delete_after=5)
                        else:
                            return await message.channel.send(
                                "<:tickNo:697759586538749982> Index must be 1 or inside the queue index.", delete_after=5)
                elif msg.startswith('vol') or msg.startswith('volume'):
                    if inVoice:
                        self.bot.logger.info(
                            f"Fresh Channel | Command volume | Ran by {message.author.name} ({message.author.id}) in guild {message.guild.name}")
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
                            return await message.channel.send(
                                "<:tickNo:697759586538749982> Volume must be a number.", delete_after=5)
                elif msg.startswith('pause') or msg.startswith('resume'):
                    if inVoice:
                        self.bot.logger.info(
                            f"Fresh Channel | Command pause/resume | Ran by {message.author.name} ({message.author.id}) in guild {message.guild.name}")
                        if player.is_playing:
                            await player.set_pause(not player.paused)
                            return await self.update_player_msg(player, message.guild, playerMsg, "pause/resume")
                elif msg.startswith('skip'):
                    if inVoice:
                        self.bot.logger.info(
                            f"Fresh Channel | Command skip | Ran by {message.author.name} ({message.author.id}) in guild {message.guild.name}")
                        if player.is_playing:
                            return await player.skip()
                elif msg.startswith('dc') or msg.startswith('disconnect'):
                    if inVoice:
                        self.bot.logger.info(
                            f"Fresh Channel | Command disconnect | Ran by {message.author.name} ({message.author.id}) in guild {message.guild.name}")
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
                    return await message.channel.send(embed=e, delete_after=30)
                else:
                    if inVoice:
                        return await self.query_request(message, player, playerMsg, msg)
            
    async def create_initial_player_message(self, channelid, guild):
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
        msg = await self.bot.get_channel(channelid).send(embed=e, view=favorites(self.bot))
        return msg.id

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

    async def create_player_msg(self, message):
        data = self.db.find_one({"_id": message.guild.id})
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
        msg = await self.bot.get_channel(data['channel']).send(embed=e, view=favorites(self.bot))
        self.db.update_one({"_id": message.guild.id}, {"$set": {"message": msg.id}})
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
            await playerMsg.edit(embed=e, view=favorites(self.bot))
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
            if player.is_playing:
                e.title = "Track Enqueued!"
                e.description = f"{track.title}\n{track.uri}"
                await message.channel.send(embed=e, delete_after=5)
        if not player.is_playing:
            player.store('channel', message.channel.id)
            await player.play()
        await self.update_player_msg(player, message.guild, playerMsg, 'basic')

    async def create_search(self, message, query):
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