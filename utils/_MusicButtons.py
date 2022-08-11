import math
import discord
import aiosqlite
from lavalink.utils import format_time

class queue_msg_buttons(discord.ui.View):
    def __init__(self, bot, guild_id, page) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.page = page
        self.guild_id = guild_id
        self.player = bot.lavalink.player_manager.get(self.guild_id)

    @discord.ui.button(label="Prev Page", style=discord.ButtonStyle.blurple)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
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
        e.set_thumbnail(url=f'https://img.youtube.com/vi/{self.player.current.identifier}/hqdefault.jpg')
        return await interaction.response.edit_message(embed=e)

    @discord.ui.button(label="Next Page", style=discord.ButtonStyle.blurple)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
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
        e.set_thumbnail(url=f'https://img.youtube.com/vi/{self.player.current.identifier}/hqdefault.jpg')
        return await interaction.response.edit_message(embed=e)

    @discord.ui.button(label="Done", style=discord.ButtonStyle.red)
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        return await interaction.message.delete()

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
        e.set_footer(text=f'Page 1/{math.ceil(len(self.player.queue) / 10)} | {len(self.player.queue)} tracks')
        e.set_thumbnail(url=f'https://img.youtube.com/vi/{self.player.current.identifier}/hqdefault.jpg')
        if len(self.player.queue) > 10:
            return await interaction.response.edit_message(embed=e, view=queue_msg_buttons(self.bot, self.guild_id, 1))
        else:
            return await interaction.response.edit_message(embed=e, view=None)

    @discord.ui.button(label="Pause/Resume", style=discord.ButtonStyle.blurple)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
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
            e.set_thumbnail(url=f'https://img.youtube.com/vi/{self.player.current.identifier}/hqdefault.jpg')
            return await interaction.response.edit_message(embed=e)
        else:
            return await interaction.response.send_message(content="Nothing playing.", ephemeral=True)

    @discord.ui.button(label="Skip", style=discord.ButtonStyle.blurple)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.player.is_playing:
            await self.player.skip()
            return await interaction.response.send_message(content="<:tickYes:697759553626046546> Skipped.", ephemeral=True)
        else:
            return await interaction.response.send_message(content="Nothing playing.", ephemeral=True)

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.red)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.player.is_playing:
            self.player.queue.clear()
            await self.player.stop()
            await interaction.response.send_message(content="⏹️ Stopped music and cleared queue.", ephemeral=True)
            return await interaction.message.delete()
        else:
            return await interaction.response.send_message(content="Nothing playing.", ephemeral=True)

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
        async with aiosqlite.connect("./data/music.db") as db:
            getData = await db.execute("SELECT musicMessage, musicToggle, musicChannel, musicRunning FROM musicSettings WHERE guild = ?", (interaction.guild.id,))
            data = await getData.fetchone()
            if data[2] == self.player.fetch('channel'):
                return await interaction.response.send_message(content="<:tickYes:697759553626046546> Replaying Track.", ephemeral=True)
            else:
                embed = discord.Embed(colour=discord.Color.blurple(), title="Replaying Track", description=f"**[{self.player.current.title}]({self.player.current.uri})**")
                return await interaction.response.edit_message(embed=embed, view=None)

    @discord.ui.button(label="Pause/Resume", style=discord.ButtonStyle.blurple)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with aiosqlite.connect("./data/music.db") as db:
            getData = await db.execute("SELECT musicMessage, musicToggle, musicChannel, musicRunning FROM musicSettings WHERE guild = ?", (interaction.guild.id,))
            data = await getData.fetchone()
            if data[2] == self.player.fetch('channel'):
                await self.player.set_pause(not self.player.paused)
                playermsg = await interaction.channel.fetch_message(data[0])
                e = discord.Embed(color=discord.Color.blurple())
                if not playermsg:
                    e.title = "Nothing Currently Playing:"
                    e.description = "Send a song `link` or `query` to play."
                    e.description += "\nSend `pause` or `resume` to control the music."
                    e.description += "\nSend `skip` to skip the current song."
                    e.description += "\nSend `prev` or `previous` to skip to the previous song."
                    e.description += "\nSend `dc` or `disconnect` to disconnect from the voice channel."
                    e.set_image(url="https://cdn.upload.systems/uploads/UCbzyCAS.jpg")
                    msg = await self.bot.get_channel(data[2]).send(embed=e)
                    await db.execute("UPDATE musicSettings SET musicMessage = ? WHERE guild = ?", (msg.id, interaction.guild.id,))
                    await db.commit()
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
                    e.set_image(url=f"https://img.youtube.com/vi/{self.player.current.identifier}/hqdefault.jpg")
                    requester = self.bot.get_user(self.player.current.requester)
                    e.set_footer(text=f"Requested by {requester.name}#{requester.discriminator}")
                    return await interaction.response.edit_message(embed=e)
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
                    e.set_image(url=f'https://img.youtube.com/vi/{self.player.current.identifier}/hqdefault.jpg')
                    e.add_field(name="Queue List:", value=queue_list, inline=False)
                    return await interaction.response.edit_message(embed=e)
            else:
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
        await interaction.response.send_message(content="<:tickYes:697759553626046546> Skipped.", ephemeral=True)
        await self.player.skip()

    @discord.ui.button(label="Stop", style=discord.ButtonStyle.red)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        async with aiosqlite.connect("./data/music.db") as db:
            getData = await db.execute("SELECT musicMessage, musicToggle, musicChannel, musicRunning FROM musicSettings WHERE guild = ?", (self.player.guild_id,))
            data = await getData.fetchone()
            if self.player.fetch('channel') == data[2]:
                channel = await self.bot.fetch_channel(data[2])
                msg = await channel.fetch_message(data[0])
                e = discord.Embed(color=discord.Color.blurple())
                e.title = "Nothing Currently Playing:"
                e.description = "Send a song `link` or `query` to play."
                e.description += "\nSend `pause` or `resume` to control the music."
                e.description += "\nSend `skip` to skip the current song."
                e.description += "\nSend `prev` or `previous` to skip to the previous song."
                e.description += "\nSend `dc` or `disconnect` to disconnect from the voice channel."
                e.set_image(url="https://cdn.upload.systems/uploads/UCbzyCAS.jpg")
                await msg.edit(embed=e, view=None)
                self.player.queue.clear()
                await self.player.stop()
                await self.bot.get_guild(int(self.player.guild_id)).voice_client.disconnect(force=True)
                self.bot.lavalink.player_manager.remove(self.player.guild_id)
        self.player.queue.clear()
        await self.player.stop()
        await interaction.response.send_message(content="⏹️ Stopped music and cleared queue.", ephemeral=True)