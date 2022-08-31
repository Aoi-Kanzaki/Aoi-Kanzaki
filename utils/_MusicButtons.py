import math
import discord
import lavalink
from aiohttp import request
from lavalink.utils import format_time
from lavalink.models import AudioTrack
from utils._LavalinkVoiceClient import LavalinkVoiceClient

class favorites(discord.ui.View):
    def __init__(self, bot) -> None:
        super().__init__(timeout=None)
        self.bot = bot

    @discord.ui.button(label="Start My Favorites", custom_id="start_fav", style=discord.ButtonStyle.green)
    async def start_fav(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bot.logger.info(f"Button Start Favs | Ran by {interaction.user.name} ({interaction.user.id}) in guild {interaction.guild.name}")
        data = self.bot.db.favorites.find_one({"_id": interaction.user.id})
        if data is None:
            return await interaction.response.send_message("You don't have any favorite songs.", ephemeral=True)
        else:
            try:
                player = self.bot.lavalink.player_manager.create(interaction.guild.id, endpoint="us")
            except Exception as error:
                print(error)
                if isinstance(error, lavalink.errors.NodeError):
                    self.bot.logger.error(f"Tried to join a voice channel in {interaction.guild.name} but there are no avaliable nodes.")
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
            return await interaction.response.send_message("I have started your favorite songs!", ephemeral=True)

class search_msg(discord.ui.View):
    def __init__(self, bot, guild_id, results) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id
        self.player = bot.lavalink.player_manager.get(guild_id)
        self.index = 0
        self.results = results
        self.db = self.bot.db.fresh_channel
        self.data = self.db.find_one({"_id": guild_id})

    @discord.ui.button(label='Last Result', emoji="<:prev:1010324780274176112>", style=discord.ButtonStyle.blurple)
    async def last_result(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index -= 1
        if self.index < 0:
            self.index = 0
        e = discord.Embed(color=discord.Color.blurple())
        e.title = 'Search Results'
        e.description = f'{self.results["tracks"][self.index]["info"]["title"]}\n{self.results["tracks"][self.index]["info"]["uri"]}'
        e.add_field(name="Author", value=self.results["tracks"][0]["info"]["author"])
        e.add_field(name="Duration", value=format_time(self.results["tracks"][self.index]["info"]["duration"]))
        picID = self.results["tracks"][self.index]["info"]["identifier"]
        e.set_thumbnail(url=f"https://img.youtube.com/vi/{picID}/hqdefault.jpg")
        return await interaction.response.edit_message(embed=e)

    @discord.ui.button(label="Play", emoji="<:play:1010305312227606610>", style=discord.ButtonStyle.blurple)
    async def play_result(self, interaction: discord.Interaction, button: discord.ui.Button):
        track = self.results['tracks'][self.index]
        embed = discord.Embed(color=discord.Color.blurple())
        embed.title = 'Track Enqueued'
        embed.description = f'[{track["info"]["title"]}]({track["info"]["uri"]})'
        track = AudioTrack(track, interaction.user.id, recommended=True)
        self.player.add(requester=interaction.user.id, track=track)
        if not self.player.is_playing:
            await self.player.play()
        await interaction.response.send_message("<:tickYes:697759553626046546> Enqueued track.", ephemeral=True)
        await interaction.message.delete()
        if self.data != None and interaction.channel.id == self.data['channel']:
            playerMsg = await interaction.channel.fetch_message(self.data['message'])
            if not playerMsg:
                playerMsg = await self.bot.get_cog('MusicChannel').create_player_msg(interaction.message)
            if self.player.current is not None:
                return await self.bot.get_cog('MusicChannel').update_player_msg(self.player, interaction.guild, playerMsg, 'basic')

    @discord.ui.button(label="Next Result", emoji="<:skip:1010321396301299742>", style=discord.ButtonStyle.blurple)
    async def next_result(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index += 1
        if self.index >= len(self.results["tracks"]):
            self.index = 0
        e = discord.Embed(color=discord.Color.blurple())
        e.title = 'Search Results'
        e.description = f'{self.results["tracks"][self.index]["info"]["title"]}\n{self.results["tracks"][self.index]["info"]["uri"]}'
        e.add_field(name="Author", value=self.results["tracks"][0]["info"]["author"])
        e.add_field(name="Duration", value=format_time(self.results["tracks"][self.index]["info"]["duration"]))
        picID = self.results["tracks"][self.index]["info"]["identifier"]
        e.set_thumbnail(url=f"https://img.youtube.com/vi/{picID}/hqdefault.jpg")
        return await interaction.response.edit_message(embed=e)

    @discord.ui.button(label="Cancel", emoji="<:stop:1010325505179918468>", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            return await interaction.delete_original_response()
        except:
            return await interaction.message.delete()

class queue_msg(discord.ui.View):
    def __init__(self, bot, guild_id, page) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.page = page
        self.guild_id = guild_id
        self.player = bot.lavalink.player_manager.get(guild_id)

    @discord.ui.button(label="Prev Page", emoji="<:prev:1010324780274176112>", style=discord.ButtonStyle.blurple)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bot.logger.info(f"Button prev_page | Ran by {interaction.user.name} ({interaction.user.id}) in guild {interaction.guild.name}")
        self.page = self.page-1
        if self.page < 1:
            self.page = math.ceil(len(self.player.queue) / 10)
        pos = format_time(self.player.position)
        if self.player.current.stream:
            dur = 'LIVE'
        else:
            dur = format_time(self.player.current.duration)
        draw_time = await self.bot.get_cog("Music").draw_time(self.guild_id)
        draw_queue = await self.bot.get_cog("Music").draw_queue(self.guild_id, self.page)
        e = discord.Embed(colour=discord.Color.blurple())
        e.add_field(name="Currently Playing:", value=f"{self.player.current.title}\n{self.player.current.uri}\n{draw_time} `[{pos}/{dur}]`")
        e.add_field(name="Up Next:", value=f"{draw_queue}", inline=False)
        e.set_footer(text=f'Page {self.page}/{math.ceil(len(self.player.queue) / 10)} | {len(self.player.queue)} tracks')
        if "open.spotify.com" in str(self.player.current.uri):
            url = f"https://open.spotify.com/oembed?url={self.player.current.uri}"
            async with request("GET", url) as response:
                json = await response.json()
                e.set_thumbnail(url=f"{json['thumbnail_url']}")
        else:
            e.set_thumbnail(url=f"https://img.youtube.com/vi/{self.player.current.identifier}/hqdefault.jpg")
        return await interaction.response.edit_message(embed=e)

    @discord.ui.button(label="Next Page", emoji="<:skip:1010321396301299742>", style=discord.ButtonStyle.blurple)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bot.logger.info(f"Button next_page | Ran by {interaction.user.name} ({interaction.user.id}) in guild {interaction.guild.name}")
        self.page = self.page+1
        if self.page > math.ceil(len(self.player.queue) / 10):
            self.page = 1
        pos = format_time(self.player.position)
        if self.player.current.stream:
            dur = 'LIVE'
        else:
            dur = format_time(self.player.current.duration)
        draw_time = await self.bot.get_cog("Music").draw_time(self.guild_id)
        draw_queue = await self.bot.get_cog("Music").draw_queue(self.guild_id, self.page)
        e = discord.Embed(colour=discord.Color.blurple())
        e.add_field(name="Currently Playing:", value=f"{self.player.current.title}\n{self.player.current.uri}\n{draw_time} `[{pos}/{dur}]`")
        e.add_field(name="Up Next:", value=f"{draw_queue}", inline=False)
        e.set_footer(text=f'Page {self.page}/{math.ceil(len(self.player.queue) / 10)} | {len(self.player.queue)} tracks')
        if "open.spotify.com" in str(self.player.current.uri):
            url = f"https://open.spotify.com/oembed?url={self.player.current.uri}"
            async with request("GET", url) as response:
                json = await response.json()
                e.set_thumbnail(url=f"{json['thumbnail_url']}")
        else:
            e.set_thumbnail(url=f"https://img.youtube.com/vi/{self.player.current.identifier}/hqdefault.jpg")
        return await interaction.response.edit_message(embed=e)

    @discord.ui.button(label="Done", emoji="<:stop:1010325505179918468>", style=discord.ButtonStyle.red)
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bot.logger.info(f"Button done | Ran by {interaction.user.name} ({interaction.user.id}) in guild {interaction.guild.name}")
        return await interaction.message.delete()

class np_msg(discord.ui.View):
    def __init__(self, bot, guild_id) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id
        self.player = bot.lavalink.player_manager.get(guild_id)

    @discord.ui.button(label="Queue", emoji="<:queue:1011747675491811458>", style=discord.ButtonStyle.blurple)
    async def queue(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bot.logger.info(f"Button queue | Ran by {interaction.user.name} ({interaction.user.id}) in guild {interaction.guild.name}")
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
        e.set_footer(text=f'Page 1/{math.ceil(len(self.player.queue) / 10)} | {len(self.player.queue)} tracks')
        if "open.spotify.com" in str(self.player.current.uri):
            url = f"https://open.spotify.com/oembed?url={self.player.current.uri}"
            async with request("GET", url) as response:
                json = await response.json()
                e.set_thumbnail(url=f"{json['thumbnail_url']}")
        else:
            e.set_thumbnail(url=f"https://img.youtube.com/vi/{self.player.current.identifier}/hqdefault.jpg")
        if len(self.player.queue) > 10:
            return await interaction.response.edit_message(embed=e, view=queue_msg(self.bot, self.guild_id, 1))
        else:
            return await interaction.response.edit_message(embed=e, view=None)

    @discord.ui.button(label="Pause", emoji="<:pause:1010305240672780348>", style=discord.ButtonStyle.blurple)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.player.paused is False:
            button.emoji = "<:play:1010305312227606610>"
            button.label = "Resume"
        else:
            button.emoji = "<:pause:1010305240672780348>"
            button.label = "Pause"
        self.bot.logger.info(f"Button pause/resume | Ran by {interaction.user.name} ({interaction.user.id}) in guild {interaction.guild.name}")
        if self.player.is_playing:
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
            if "open.spotify.com" in str(self.player.current.uri):
                url = f"https://open.spotify.com/oembed?url={self.player.current.uri}"
                async with request("GET", url) as response:
                    json = await response.json()
                    e.set_thumbnail(url=f"{json['thumbnail_url']}")
            else:
                e.set_thumbnail(url=f"https://img.youtube.com/vi/{self.player.current.identifier}/hqdefault.jpg")
            return await interaction.response.edit_message(embed=e, view=self)
        else:
            return await interaction.response.send_message(content="Nothing playing.", ephemeral=True)

    @discord.ui.button(label="Skip", emoji= "<:skip:1010321396301299742>", style=discord.ButtonStyle.blurple)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bot.logger.info(f"Button skip | Ran by {interaction.user.name} ({interaction.user.id}) in guild {interaction.guild.name}")
        if self.player.is_playing:
            await self.player.skip()
            return await interaction.response.send_message(content="<:tickYes:697759553626046546> Skipped.", ephemeral=True)
        else:
            return await interaction.response.send_message(content="Nothing playing.", ephemeral=True)

    @discord.ui.button(label="Stop", emoji="<:stop:1010325505179918468>", style=discord.ButtonStyle.red)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bot.logger.info(f"Button stop | Ran by {interaction.user.name} ({interaction.user.id}) in guild {interaction.guild.name}")
        if self.player.is_playing:
            self.player.queue.clear()
            await self.player.stop()
            await interaction.response.send_message(content="⏹️ Stopped music and cleared queue.", ephemeral=True)
            return await interaction.message.delete()
        else:
            return await interaction.response.send_message(content="Nothing playing.", ephemeral=True)

class event_hook(discord.ui.View):
    def __init__(self, bot, guild_id) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.fav = self.bot.db.favorites
        self.player = bot.lavalink.player_manager.get(guild_id)
        self.db = self.bot.db.fresh_channel
        self.data = self.db.find_one({"_id": guild_id})

    @discord.ui.button(label="Love", emoji="🤍", style=discord.ButtonStyle.blurple)
    async def love_song(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bot.logger.info(f"Button love | Ran by {interaction.user.name} ({interaction.user.id}) in guild {interaction.guild.name}")
        data = self.fav.find_one({"_id": interaction.user.id})
        if data is None:
            self.fav.insert_one({"_id": interaction.user.id})
            self.fav.update_one({"_id": interaction.user.id}, {"$set": {"songs": []}})
        self.fav.update_one({"_id": interaction.user.id}, {"$push": {"songs": self.player.current.uri}})
        return await interaction.response.send_message(
            "<:tickYes:697759553626046546> Done, it's now added to your favorites!", ephemeral=True)

    @discord.ui.button(label="Previous", emoji="<:prev:1010324780274176112>", style=discord.ButtonStyle.blurple)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bot.logger.info(f"Button previous | Ran by {interaction.user.name} ({interaction.user.id}) in guild {interaction.guild.name}")
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
        if self.data != None and interaction.channel.id == self.data['channel']:
            return await interaction.response.send_message(content="<:tickYes:697759553626046546> Replaying Track.", ephemeral=True)
        else:
            embed = discord.Embed(colour=discord.Color.blurple(), title="Replaying Track", description=f"**[{self.player.current.title}]({self.player.current.uri})**")
            return await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Pause", emoji="<:pause:1010305240672780348>", style=discord.ButtonStyle.blurple)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bot.logger.info(f"Button pause/resume | Ran by {interaction.user.name} ({interaction.user.id}) in guild {interaction.guild.name}")
        if self.player.paused is False:
            button.emoji = "<:play:1010305312227606610>"
            button.label = "Resume"
        else:
            button.emoji = "<:pause:1010305240672780348>"
            button.label = "Pause"
        if self.data != None and interaction.channel.id == self.data['channel']:
            await self.player.set_pause(not self.player.paused)
            playermsg = await interaction.channel.fetch_message(self.data['message'])
            e = discord.Embed(color=discord.Color.blurple())
            if not playermsg:
                e.title = "Nothing Currently Playing:"
                e.description = "Send a song `link` or `query` to play."
                e.description += "\nSend `pause` or `resume` to control the music."
                e.description += "\nSend `skip` to skip the current song."
                e.description += "\nSend `dc` or `disconnect` to disconnect from the voice channel."
                e.description += "\nSend `vol 10` or `volume 10` to change the volume."
                e.description += "\nSend `rem 1` or `remove 1` to remove a song from the queue."
                e.description += "\nSend `search <query>` to search for a song."
                e.set_image(url="https://i.imgur.com/VIYaATs.jpg")
                msg = await self.bot.get_channel(self.data['channel']).send(embed=e, view=favorites(self.bot))
                self.db.update_one({"_id": interaction.guild.id}, {"$set": {"message": msg.id}})
                playermsg = await interaction.channel.fetch_message(msg.id)
            if self.player.paused == False:
                if self.player.current.stream:
                    dur = 'LIVE'
                else:
                    dur = format_time(self.player.current.duration)
                if self.player.queue:
                    queue_list = ''
                    for i, track in enumerate(self.player.queue[(1 - 1) * 5:(1 - 1) * 5 + 5], start=(1 - 1) * 5):
                        queue_list += '`{}.` {}\n'.format(i + 1, track.title)
                else:
                    queue_list = "Join a voice channel and queue songs by name or url in here."
                kek = f"{self.player.current.title}\n{self.player.current.uri}"
                e.add_field(name="Currently Playing:", value=kek, inline=False)
                e.add_field(name="Author:", value=self.player.current.author)
                e.add_field(name="Duration:", value=dur)
                e.add_field(name="Queue List:", value=queue_list, inline=False)
                if "open.spotify.com" in str(self.player.current.uri):
                    url = f"https://open.spotify.com/oembed?url={self.player.current.uri}"
                    async with request("GET", url) as response:
                        json = await response.json()
                        e.set_image(url=f"{json['thumbnail_url']}")
                else:
                    e.set_image(url=f"https://img.youtube.com/vi/{self.player.current.identifier}/hqdefault.jpg")
                requester = self.bot.get_user(self.player.current.requester)
                e.set_footer(text=f"Requested by {requester.name}#{requester.discriminator}")
                return await interaction.response.edit_message(embed=e, view=self)
            else:
                if self.player.queue:
                    queue_list = ''
                    for i, track in enumerate(self.player.queue[(1 - 1) * 10:(1 - 1) * 10 + 10], start=(1 - 1) * 10):
                        queue_list += '`{}.` {}\n'.format(i + 1, track.title)
                else:
                    queue_list = "Join a voice channel and queue songs by name or url in here."
                e.title = "Paused:"
                e.description = f"{self.player.current.title}\n"
                e.description += f"{self.player.current.uri}\n"
                if "open.spotify.com" in str(self.player.current.uri):
                    url = f"https://open.spotify.com/oembed?url={self.player.current.uri}"
                    async with request("GET", url) as response:
                        json = await response.json()
                        e.set_thumbnail(url=f"{json['thumbnail_url']}")
                else:
                    e.set_thumbnail(url=f"https://img.youtube.com/vi/{self.player.current.identifier}/hqdefault.jpg")
                e.add_field(name="Queue List:", value=queue_list, inline=False)
                return await interaction.response.edit_message(embed=e, view=self)
        else:
            await self.player.set_pause(not self.player.paused)
            e = discord.Embed(colour=discord.Color.blurple())
            if self.player.paused is True:
                e.title = "Paused:"
            else:
                e.title = "Now Playing:"
            e.description = f"{self.player.current.title}\n"
            e.description += f"{self.player.current.uri}\n"
            if "open.spotify.com" in str(self.player.current.uri):
                url = f"https://open.spotify.com/oembed?url={self.player.current.uri}"
                async with request("GET", url) as response:
                    json = await response.json()
                    e.set_thumbnail(url=f"{json['thumbnail_url']}")
            else:
                e.set_thumbnail(url=f"https://img.youtube.com/vi/{self.player.current.identifier}/hqdefault.jpg")
            if self.player.queue:
                number = 0
                upNext = ""
                for track in self.player.queue[0:5]:
                    number += 1
                    upNext += f"`{number})` {track.title}\n"
                e.add_field(name="Up Next:", value=upNext)
            return await interaction.response.edit_message(embed=e, view=self)

    @discord.ui.button(label="Skip", emoji="<:skip:1010321396301299742>", style=discord.ButtonStyle.blurple)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bot.logger.info(f"Button skip | Ran by {interaction.user.name} ({interaction.user.id}) in guild {interaction.guild.name}")
        await interaction.response.send_message(content="<:tickYes:697759553626046546> Skipped.", ephemeral=True)
        await self.player.skip()

    @discord.ui.button(label="Stop", emoji="<:stop:1010325505179918468>", style=discord.ButtonStyle.red)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bot.logger.info(f"Button stop | Ran by {interaction.user.name} ({interaction.user.id}) in guild {interaction.guild.name}")
        if self.data != None and interaction.channel.id == self.data['channel']:
            channel = await self.bot.fetch_channel(self.data['channel'])
            msg = await channel.fetch_message(self.data['message'])
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
            self.player.queue.clear()
            await self.player.stop()
            vc = self.bot.get_guild(int(self.player.guild_id)).voice_client
            if vc:
                await self.bot.get_guild(int(self.player.guild_id)).voice_client.disconnect(force=True)
            self.bot.lavalink.player_manager.remove(self.player.guild_id)
            self.bot.logger.info(f"Fresh Channel | Button stop | Ran by {interaction.user.name} ({interaction.user.id}) in guild {interaction.guild.name}")
        self.player.queue.clear()
        await self.player.stop()
        await interaction.response.send_message(content="⏹️ Stopped music and cleared queue.", ephemeral=True)