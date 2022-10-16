import re
import discord
import asyncio
import datetime
import humanize
from aiohttp import request
from discord.ext import commands
from discord import app_commands as Fresh
from buttons.SearchMessage import SearchButtons
from utils.LavalinkVoiceClient import LavalinkVoiceClient
from buttons.MusicChannel import PlayingButtons, DefaultButtons


class MusicChannel(commands.GroupCog,
                   name="musicchannel",
                   description="All music channel related commands."):

    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.db = self.bot.db.musicChannel
        self.bot.add_view(DefaultButtons(self.bot))

    @Fresh.command(name="enable")
    async def enable(self, interaction: discord.Interaction):
        """Enabled the music channel."""
        data = self.db.find_one({"_id": interaction.guild.id})
        if not data:
            channel = await interaction.guild.create_text_channel(name="fresh-music")
            controllerEmbed = discord.Embed(
                colour=discord.Colour.teal(),
                description="Send a song link or query to start playing music!\nOr click the button to start you favorite songs!",
            )
            controllerEmbed.set_author(
                name=f"{self.bot.user.name} Music:",
                icon_url=self.bot.user.avatar
            )
            controllerEmbed.set_image(url=self.bot.user.avatar)
            controllerMessage = await channel.send(embed=controllerEmbed,
                                                   view=DefaultButtons(self.bot))
            data = {"_id": interaction.guild.id, "toggle": True,
                    "channel": channel.id, "message": controllerMessage.id}
            self.db.insert_one(data)
            return await interaction.response.send_message(
                content="I have enabled the music channel in this server!",
                ephemeral=True
            )
        else:
            return await interaction.response.send_message(
                content="The music channel is already enabled in this server!",
                ephemeral=True
            )

    @Fresh.command(name="disable")
    async def disable(self, interaction: discord.Interaction):
        """Disables the music channel."""
        data = self.db.find_one({"_id": interaction.guild.id})
        if data:
            channel = await self.bot.fetch_channel(data['channel'])
            await channel.delete()
            self.db.delete_one(data)
            return await interaction.response.send_message(
                content="I have disabled the music channel!",
                ephemeral=True
            )
        else:
            return await interaction.response.send_message(
                content="The music channel is not enabled in this server!",
                ephemeral=True
            )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if not message.guild:
            return
        if message.author.bot:
            return
        data = self.db.find_one({"_id": message.guild.id})
        if not data:
            return
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
                if msg.startswith('cancel') or msg.startswith('start'):
                    return
                elif msg.startswith('search'):
                    if inVoice:
                        return await self.create_search(message, msg.replace('search', ''))
                elif msg.startswith('rem') or msg.startswith('remove'):
                    index = msg.replace('rem', '').replace(
                        'ove', '').replace(' ', '')
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
                    volume = msg.replace('vol', '').replace(
                        'ume', '').replace(' ', '')
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
                    if player.is_playing:
                        await player.set_pause(not player.paused)
                        return await self.update_player_msg(player, message.guild, playerMsg, "pause/resume")
                elif msg.startswith('skip'):
                    if player.is_playing:
                        return await player.skip()
                elif msg.startswith('dc') or msg.startswith('disconnect'):
                    await message.guild.voice_client.disconnect(force=True)
                    await self.update_player_msg(player, message.guild, playerMsg, "main")
                    return self.bot.lavalink.player_manager.remove(message.guild.id)
                elif msg.startswith('help'):
                    e = discord.Embed(color=discord.Colour.teal())
                    e.description = "Send a song `link` or `query` to play."
                    e.description += "\nSend `pause` or `resume` to control the music."
                    e.description += "\nSend `skip` to skip the current song."
                    e.description += "\nSend `prev` or `previous` to skip to the previous song."
                    e.description += "\nSend `dc` or `disconnect` to disconnect from the voice channel."
                    e.description += "\nSend `vol 10` or `volume 10` to change the volume."
                    e.description += "\nSend `rem 1` or `remove 1` to remove a song from the queue."
                    e.description += "\nSend `search <query>` to search for a song."
                    e.description += "\nSend `stop` to stop the player."
                    e.set_footer(
                        text="This message will delete in 30 seconds.")
                    return await message.channel.send(embed=e, delete_after=30)
                else:
                    return await self.query_request(message, player, playerMsg, msg)

    async def update_player_msg(self, player, guild, playerMsg, status):
        if status == "main":
            e = discord.Embed(color=discord.Colour.teal())
            e.set_author(name="Fresh Music", icon_url=self.bot.user.avatar.url)
            e.description = "Send a song link or query to start playing music!\n"
            e.description += "Or click the button to start you favorite songs!"
            e.set_image(url="https://i.imgur.com/VIYaATs.jpg")
            await playerMsg.edit(embed=e, view=DefaultButtons(self.bot))
        else:
            if player.queue:
                queueList = ''
                for index, track in enumerate(player.queue[0:5], start=0):
                    queueList += f'`{index+1}.` [{track.title}]({track.uri})\n'
            else:
                queueList = "Join a voice channel and queue songs by name or url in here."
            if player.current.stream:
                dur = '🔴 LIVE'
            else:
                dur = player.current.duration
                delta = datetime.timedelta(milliseconds=dur)
                dur = humanize.naturaldelta(delta)
            current = f"**{player.current.title} - {player.current.author}**\n*[Link to Song]({player.current.uri})*"
            e = discord.Embed(color=discord.Colour.teal())
            if "open.spotify.com" in str(player.current.uri):
                url = f"https://open.spotify.com/oembed?url={player.current.uri}"
                async with request("GET", url) as response:
                    json = await response.json()
                    image = json['thumbnail_url']
            else:
                image = f"https://img.youtube.com/vi/{player.current.identifier}/hqdefault.jpg"
            if status == 'pause/resume':
                if player.paused == True:
                    e.title = "Paused:"
                    e.description = f"{player.current.title}\n{player.current.uri}"
                    e.add_field(name="Queue List:", value=queueList)
                    e.set_thumbnail(url=image)
                else:
                    e.title = "Currently Playing:"
                    e.description = current
                    e.add_field(name="Duration:", value=dur)
                    e.add_field(name="Requested By:",
                                value=f"<@!{player.current.requester}>")
                    e.add_field(name="Queue List:",
                                value=queueList, inline=False)
                    e.set_image(url=image)
            elif status == "basic":
                e.title = "Currently Playing:"
                e.description = current
                e.add_field(name="Duration:", value=dur)
                e.add_field(name="Requested By:",
                            value=f"<@!{player.current.requester}>")
                e.add_field(name="Queue List:", value=queueList, inline=False)
                e.set_image(url=image)
            await playerMsg.edit(embed=e, view=PlayingButtons(self.bot, guild.id))

    async def query_request(self, message, player, playerMsg, query: str.strip('<>')):
        player = self.bot.lavalink.player_manager.players.get(message.guild.id)
        query = query.strip('<>')
        e = discord.Embed(color=discord.Colour.teal())
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
            e = discord.Embed(color=discord.Colour.teal())
            e.title = 'Search Results'
            e.description = f'{results["tracks"][0]["info"]["title"]}\n{results["tracks"][0]["info"]["uri"]}'
            e.add_field(name="Author",
                        value=results["tracks"][0]["info"]["author"])
            dur = results["tracks"][0]["info"]["duration"]
            delta = datetime.timedelta(milliseconds=dur)
            duration = humanize.naturaldelta(delta)
            e.add_field(name="Duration", value=duration)
            picID = results["tracks"][0]["info"]["identifier"]
            e.set_thumbnail(
                url=f"https://img.youtube.com/vi/{picID}/hqdefault.jpg")
            await message.channel.send(embed=e, view=SearchButtons(self.bot, message.guild.id, results))

    async def check_voice(self, message):
        if not message.author.voice or not message.author.voice.channel:
            await message.channel.send('<:tickNo:697759586538749982> Join a voicechannel first.', delete_after=5)
            return False
        if not message.author.voice.channel.permissions_for(message.guild.me).connect or not message.author.voice.channel.permissions_for(message.guild.me).speak:
            await message.channel.send('<:tickNo:697759586538749982> I need the `CONNECT` and `SPEAK` permissions.', delete_after=5)
            return False
        return True

    async def create_player(self, message):
        inVoice = await self.check_voice(message)
        if inVoice:
            player = self.bot.lavalink.player_manager.create(
                message.guild.id, endpoint="us")
            if player.channel_id is not None:
                if int(player.channel_id) != message.author.voice.channel.id:
                    await message.channel.send('<:tickNo:697759586538749982> You need to be in my voicechannel.', delete_after=5)
                    return False
            if not player.is_connected:
                player.store('channel', message.channel.id)
                await message.author.voice.channel.connect(cls=LavalinkVoiceClient)
            return player

    async def create_player_msg(self, message):
        data = self.db.find_one({"_id": message.guild.id})
        e = discord.Embed(color=discord.Colour.teal())
        e.set_author(name="Fresh Music", icon_url=self.bot.user.avatar.url)
        e.description = "Send a song link or query to start playing music!\n"
        e.description += "Or click the button to start you favorite songs!"
        e.set_image(url=self.bot.user.avatar)
        msg = await self.bot.get_channel(data['channel']).send(embed=e, view=DefaultButtons(self.bot))
        self.db.update_one({"_id": message.guild.id}, {
                           "$set": {"message": msg.id}})
        return await message.channel.fetch_message(msg.id)

    async def cog_unload(self):
        self.bot.lavalink._event_hooks.clear()
        for guild in self.bot.guilds:
            data = self.db.find_one({"_id": guild.id})
            if data != None and data['toggle'] is True:
                try:
                    channel = await guild.fetch_channel(data['channel'])
                    msg = await channel.fetch_message(data['message'])
                    e = discord.Embed(color=discord.Colour.teal())
                    controllerEmbed = discord.Embed(
                        colour=discord.Colour.teal(),
                        description="Send a song link or query to start playing music!\nOr click the button to start you favorite songs!",
                    )
                    controllerEmbed.set_author(
                        name=f"{self.bot.user.name} Music:",
                        icon_url=self.bot.user.avatar
                    )
                    controllerEmbed.set_image(url=self.bot.user.avatar)
                    await msg.edit(embed=controllerEmbed, view=DefaultButtons(self.bot))
                    await asyncio.sleep(1)
                except discord.errors.NotFound:
                    pass


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(MusicChannel(bot))
