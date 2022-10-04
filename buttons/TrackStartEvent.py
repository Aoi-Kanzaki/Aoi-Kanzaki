import discord
import lavalink
from aiohttp import request
from sources.spotify import SpotifyAudioTrack, SpotifySource
from buttons.EnsureChoice import EnsureChoiceButtons


class TrackStartEventButtons(discord.ui.View):
    def __init__(self, bot, guild_id) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.fav = self.bot.db.favorites
        self.player = bot.lavalink.player_manager.get(guild_id)

    @discord.ui.button(emoji="🤍", style=discord.ButtonStyle.grey)
    async def love_song(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = self.fav.find_one({"_id": interaction.user.id})
        if data is None:
            self.fav.insert_one({"_id": interaction.user.id})
            self.fav.update_one({"_id": interaction.user.id}, {
                                "$set": {"songs": [self.player.current.uri]}})
            return await interaction.response.send_message(
                "<:tickYes:697759553626046546> Done, it's now added to your favorites!", ephemeral=True)
        else:
            if self.player.current.uri in data['songs']:
                e = discord.Embed(colour=discord.Colour.red())
                e.set_author(
                    name=interaction.user.display_name, icon_url=interaction.user.display_avatar)
                e.description = "This song seems to already be in your favorite songs?\n"
                e.description += "Would you like to remove it?"
                await interaction.response.send_message(
                    embed=e, view=EnsureChoiceButtons(self.bot, self.player.current.uri), ephemeral=True)
            else:
                self.fav.update_one({"_id": interaction.user.id}, {
                                    "$push": {"songs": self.player.current.uri}})
                return await interaction.response.send_message(
                    "<:tickYes:697759553626046546> Done, it's now added to your favorites!", ephemeral=True)

    @discord.ui.button(emoji="<:pause:1010305240672780348>", style=discord.ButtonStyle.gray)
    async def pause(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.player.set_pause(not self.player.paused)
        if self.player.paused:
            title = "Paused"
            button.emoji = "<:play:1010305312227606610>"
        else:
            button.emoji = "<:pause:1010305240672780348>"
            title = "Now Playing"
        e = discord.Embed(colour=0x93B1B4, title=title)
        duration = '🔴 LIVE' if self.player.current.stream else lavalink.utils.format_time(
            self.player.current.duration)
        fmt = f'{self.player.current.title} - {self.player.current.author}' \
            if isinstance(self.player.current, SpotifyAudioTrack) else self.player.current.title
        e.description = f'**[{fmt}]({self.player.current.uri})**\n*Duration: {duration}*\n*Requested By: <@!{self.player.current.requester}>*'
        if "open.spotify.com" in str(self.player.current.uri):
            url = f"https://open.spotify.com/oembed?url={self.player.current.uri}"
            async with request("GET", url) as response:
                json = await response.json()
                e.set_thumbnail(url=f"{json['thumbnail_url']}")
        else:
            e.set_thumbnail(
                url=f"https://img.youtube.com/vi/{self.player.current.identifier}/hqdefault.jpg")
        return await interaction.response.edit_message(embed=e, view=self)

    @discord.ui.button(emoji="<:skip:1010321396301299742>", style=discord.ButtonStyle.grey)
    async def skip(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.player.is_playing:
            await self.player.skip()
        else:
            return await interaction.response.send_message(
                content="Nothing playing.",
                ephemeral=True
            )

    @discord.ui.button(emoji="<:stop:1010325505179918468>", style=discord.ButtonStyle.red)
    async def stop(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.player.queue.clear()
        await self.player.stop()
        await interaction.response.send_message(content="⏹️ Stopped music and cleared queue.", ephemeral=True)
