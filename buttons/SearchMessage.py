import discord
import datetime
import humanize
from lavalink.models import AudioTrack


class SearchButtons(discord.ui.View):
    def __init__(self, bot, guild_id, results) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.guild_id = guild_id
        self.player = bot.lavalink.player_manager.get(guild_id)
        self.index = 0
        self.results = results
        self.db = self.bot.db.musicChannel

    @discord.ui.button(label='Last Result', emoji="<:prev:1010324780274176112>", style=discord.ButtonStyle.blurple)
    async def last_result(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index -= 1
        if self.index < 0:
            self.index = 0
        e = discord.Embed(color=discord.Colour.teal())
        e.title = 'Search Results'
        e.description = f'{self.results["tracks"][self.index]["info"]["title"]}\n{self.results["tracks"][self.index]["info"]["uri"]}'
        e.add_field(name="Author",
                    value=self.results["tracks"][0]["info"]["author"])
        dur = self.results["tracks"][self.index]["info"]["duration"]
        delta = datetime.timedelta(milliseconds=dur)
        duration = humanize.naturaldelta(delta)
        e.add_field(name="Duration", value=duration)
        picID = self.results["tracks"][self.index]["info"]["identifier"]
        e.set_thumbnail(
            url=f"https://img.youtube.com/vi/{picID}/hqdefault.jpg")
        return await interaction.response.edit_message(embed=e)

    @discord.ui.button(label="Play", emoji="<:play:1010305312227606610>", style=discord.ButtonStyle.blurple)
    async def play_result(self, interaction: discord.Interaction, button: discord.ui.Button):
        track = self.results['tracks'][self.index]
        embed = discord.Embed(color=discord.Colour.teal())
        embed.title = 'Track Enqueued'
        embed.description = f'[{track["info"]["title"]}]({track["info"]["uri"]})'
        track = AudioTrack(track, interaction.user.id, recommended=True)
        self.player.add(requester=interaction.user.id, track=track)
        if not self.player.is_playing:
            await self.player.play()
        await interaction.response.send_message("<:tickYes:697759553626046546> Enqueued track.", ephemeral=True)
        await interaction.message.delete()
        data = await self.db.find_one({"_id": self.guild_id})
        if data != None and interaction.channel.id == data['channel']:
            playerMsg = await interaction.channel.fetch_message(data['message'])
            if not playerMsg:
                playerMsg = await self.bot.get_cog('MusicChannel').create_player_msg(interaction.message)
            if self.player.current is not None:
                return await self.bot.get_cog('MusicChannel').update_player_msg(self.player, interaction.guild, playerMsg, 'basic')

    @discord.ui.button(label="Next Result", emoji="<:skip:1010321396301299742>", style=discord.ButtonStyle.blurple)
    async def next_result(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index += 1
        if self.index >= len(self.results["tracks"]):
            self.index = 0
        e = discord.Embed(color=discord.Colour.teal())
        e.title = 'Search Results'
        e.description = f'{self.results["tracks"][self.index]["info"]["title"]}\n{self.results["tracks"][self.index]["info"]["uri"]}'
        e.add_field(name="Author",
                    value=self.results["tracks"][0]["info"]["author"])
        dur = self.results["tracks"][self.index]["info"]["duration"]
        delta = datetime.timedelta(milliseconds=dur)
        duration = humanize.naturaldelta(delta)
        e.add_field(name="Duration", value=duration)
        picID = self.results["tracks"][self.index]["info"]["identifier"]
        e.set_thumbnail(
            url=f"https://img.youtube.com/vi/{picID}/hqdefault.jpg")
        return await interaction.response.edit_message(embed=e)

    @discord.ui.button(label="Cancel", emoji="<:stop:1010325505179918468>", style=discord.ButtonStyle.red)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            return await interaction.delete_original_response()
        except:
            return await interaction.message.delete()
