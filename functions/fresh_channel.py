import re
import discord
import aiosqlite
import asyncio
from discord.ext import commands
from lavalink.models import AudioTrack
from lavalink.utils import format_time
from utils._LavalinkVoiceClient import LavalinkVoiceClient
from utils._MusicButtons import np_msg_buttons

class MusicChannel(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        query = message.content
        if message.author.bot: return
        if message.content.startswith("ft?") or message.content.startswith("f?"): return
        async with aiosqlite.connect("./data/music.db") as db:
            getData = await db.execute("SELECT musicMessage, musicToggle, musicChannel, musicRunning FROM musicSettings WHERE guild = ?", (message.guild.id,))
            data = await getData.fetchone()
            if not data: return
            if data[1] == 1:
                if message.channel.id == data[2]:
                    await asyncio.sleep(0.5)
                    await message.delete()
                    player = self.bot.lavalink.player_manager.create(message.guild.id, endpoint="us")
                    if not message.author.voice or not message.author.voice.channel:
                            return await message.channel.send('<:tickNo:697759586538749982> Join a voicechannel first.', delete_after=5)
                    if not message.author.voice.channel.permissions_for(message.guild.me).connect or not message.author.voice.channel.permissions_for(message.guild.me).speak:
                        return await message.channel.send('<:tickNo:697759586538749982> I need the `CONNECT` and `SPEAK` permissions.', delete_after=5)
                    if player.channel_id is not None:
                        if int(player.channel_id) != message.author.voice.channel.id:
                            return await message.channel.send('<:tickNo:697759586538749982> You need to be in my voicechannel.', delete_after=5)
                    if not player.is_connected:
                        player.store('channel', message.channel.id)
                        await message.author.voice.channel.connect(cls=LavalinkVoiceClient)
                    playermsg = await message.channel.fetch_message(data[0])
                    if not playermsg:
                        e = discord.Embed(color=discord.Color.blurple())
                        e.title = "Nothing Currently Playing:"
                        e.description = "Send a song `link` or `query` to play."
                        e.description += "\nSend `pause` or `resume` to control the music."
                        e.description += "\nSend `skip` to skip the current song."
                        e.description += "\nSend `dc` or `disconnect` to disconnect from the voice channel."
                        e.set_image(url="https://cdn.upload.systems/uploads/UCbzyCAS.jpg")
                        msg = await self.bot.get_channel(data[2]).send(embed=e)
                        await db.execute("UPDATE musicSettings SET musicMessage = ? WHERE guild = ?", (msg.id, message.guild.id,))
                        await db.commit()
                        playermsg = await message.channel.fetch_message(msg.id)
                    if query not in ('pause', 'resume', 'skip', 'dc', 'disconnect', 'prev', 'previous'):
                        query = query.strip('<>')
                        if "open.spotify.com" in query:
                            query = "{}".format(re.sub(r"(http[s]?:\/\/)?(open.spotify.com)\/", "", query).replace("/", ":"))
                            await self.bot.get_cog('Music').queue_spotify(message, player, query)
                        if not re.compile(r'https?://(?:www\.)?.+').match(query):
                            query = f'ytsearch:{query}'
                        results = await player.node.get_tracks(query)
                        if not results or not results['tracks']:
                            return await message.channel.send('Nothing found!', delete_after=5)
                        if results['loadType'] == 'LOAD_FAILED':
                            return await message.channel.send('Oh no, something failed. Please try again.', delete_after=5)
                        if results['loadType'] == 'PLAYLIST_LOADED':
                            tracks = results['tracks']
                            for track in tracks:
                                player.add(requester=message.author.id, track=track)
                            if not player.is_playing:
                                await player.play()
                            e = discord.Embed(color=discord.Color.blurple())
                            queue_list = ''
                            for i, track in enumerate(player.queue[(1 - 1) * 5:(1 - 1) * 5 + 5], start=(1 - 1) * 5):
                                queue_list += '`{}.` {}\n'.format(i + 1, track.title)
                            if player.current.stream:
                                dur = 'LIVE'
                            else:
                                dur = format_time(player.current.duration)
                            e.add_field(name="Title:", value=player.current.title, inline=False)
                            e.add_field(name="Position:", value=f"{await self.draw_time(player.guild_id)} `[{format_time(player.position)}/{dur}]`\n", inline=False)
                            e.add_field(name="Queue List:", value=queue_list, inline=False)
                            e.set_image(url=f'https://img.youtube.com/vi/{player.current.identifier}/hqdefault.jpg')
                            requester = self.bot.get_user(player.current.requester)
                            e.set_footer(text=f"Requested by {requester.name}#{requester.discriminator}")
                            await playermsg.edit(embed=e)
                        else:
                            e = discord.Embed(color=discord.Color.blurple())
                            track = results['tracks'][0]
                            track = AudioTrack(track, message.author.id, recommended=True)
                            player.add(requester=message.author.id, track=track)
                            if not player.is_playing:
                                await player.play()
                            if player.queue:
                                if player.current.stream:
                                    dur = 'LIVE'
                                else:
                                    dur = format_time(player.current.duration)
                                queue_list = ''
                                for i, track in enumerate(player.queue[(1 - 1) * 5:(1 - 1) * 5 + 5], start=(1 - 1) * 5):
                                    queue_list += '`{}.` {}\n'.format(i + 1, track.title)
                                e.add_field(name="Title:", value=player.current.title, inline=False)
                                e.add_field(name="Position:", value=f"{await self.bot.get_cog('Music').draw_time(player.guild_id)} `[{format_time(player.position)}/{dur}]`\n", inline=False)
                                e.add_field(name="Queue List:", value=queue_list, inline=False)
                                e.set_image(url=f"https://img.youtube.com/vi/{player.current.identifier}/hqdefault.jpg")
                                e.set_footer(text=f"Requested by {message.author.name}#{message.author.discriminator}")
                                await playermsg.edit(embed=e)
                    elif query in ('dc', 'disconnect'):
                        if player.is_connected:
                            await message.guild.voice_client.disconnect(force=True)
                            e = discord.Embed(color=discord.Color.blurple())
                            e.title = "Nothing Currently Playing:"
                            e.description = "Send a song `link` or `query` to play."
                            e.description += "\nSend `pause` or `resume` to control the music."
                            e.description += "\nSend `skip` to skip the current song."
                            e.description += "\nSend `prev` or `previous` to skip to the previous song."
                            e.description += "\nSend `dc` or `disconnect` to disconnect from the voice channel."
                            e.set_image(url="https://cdn.upload.systems/uploads/UCbzyCAS.jpg")
                            await playermsg.edit(embed=e)
                            return self.bot.lavalink.player_manager.remove(message.guild.id)
                    elif query in ('pause', 'resume'):
                        if not player.is_playing:
                            return
                        await player.set_pause(not player.paused)
                        if player.queue:
                            queue_list = ''
                            for i, track in enumerate(player.queue[(1 - 1) * 5:(1 - 1) * 5 + 5], start=(1 - 1) * 5):
                                queue_list += '`{}.` {}\n'.format(i + 1, track.title)
                        else:
                            queue_list = "Join a voice channel and queue songs by name or url in here."
                        e = discord.Embed(color=discord.Color.blurple())
                        if player.paused == True:
                            e.title = "The music is currently paused"
                            e.add_field(name="Title:", value=player.current.title, inline=False)
                            e.set_image(url=f"https://img.youtube.com/vi/{player.current.identifier}/hqdefault.jpg")
                            e.set_footer(text=f"Requested by {message.author.name}#{message.author.discriminator}")
                            await playermsg.edit(embed=e)
                        else:
                            if player.current.stream:
                                dur = 'LIVE'
                            else:
                                dur = format_time(player.current.duration)
                            e.add_field(name="Title:", value=player.current.title, inline=False)
                            e.add_field(name="Position:", value=f"{await self.bot.get_cog('Music').draw_time(player.guild_id)} `[{format_time(player.position)}/{dur}]`\n", inline=False)
                            e.add_field(name="Queue List:", value=queue_list, inline=False)
                            e.set_image(url=f"https://img.youtube.com/vi/{player.current.identifier}/hqdefault.jpg")
                            e.set_footer(text=f"Requested by {message.author.name}#{message.author.discriminator}")
                            await playermsg.edit(embed=e)
                    elif query == 'skip':
                        await player.skip()
                        

async def setup(bot):
    await bot.add_cog(MusicChannel(bot))