import math
import discord
import humanize
import datetime


class QueueButtons(discord.ui.View):
    def __init__(self, bot, guild_id, page) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.page = page
        self.guild_id = guild_id
        self.player = bot.lavalink.player_manager.get(guild_id)

    @discord.ui.button(label="Prev Page", emoji="<:prev:1010324780274176112>", style=discord.ButtonStyle.blurple)
    async def prev_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = self.page-1
        if self.page < 1:
            self.page = math.ceil(len(self.player.queue) / 10)
        embed = await self.draw_queue(interaction)
        return await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="Next Page", emoji="<:skip:1010321396301299742>", style=discord.ButtonStyle.blurple)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page = self.page+1
        if self.page > math.ceil(len(self.player.queue) / 10):
            self.page = 1
        embed = await self.draw_queue(interaction)
        return await interaction.response.edit_message(embed=embed)

    @discord.ui.button(label="Done", emoji="<:stop:1010325505179918468>", style=discord.ButtonStyle.red)
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        return await interaction.message.delete()

    async def draw_queue(self, interaction: discord.Interaction):
        itemsPerPage = 10
        pages = math.ceil(len(self.player.queue) / itemsPerPage)
        if self.page < 1:
            self.page = pages
        elif self.page > pages:
            self.page = 1
        start = (self.page - 1) * itemsPerPage
        end = start + itemsPerPage
        queueList = ''
        queueDur = 0
        for index, track in enumerate(self.player.queue[start:end], start=start):
            queueList += f'`{index+1}.` {track.title} - {track.author}\n'
            queueDur += track.duration
        embed = discord.Embed(colour=discord.Colour.teal(),
                              description=f'{queueList}')
        queueDur = humanize.naturaldelta(
            datetime.timedelta(milliseconds=queueDur))
        embed.set_footer(
            text=f'Viewing page {self.page}/{pages} | Queue Duration: {queueDur} | Tracks: {len(self.player.queue)}')
        return embed

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        self.bot.logger.error(f"[Queue Buttons] Error: {error}")
        e = discord.Embed(
            colour=discord.Colour.red(),
            title="An error has occurred!"
        )
        e.add_field(name="Error", value=error)
        e.set_thumbnail(self.bot.user.avatar)
        try:
            return await interaction.response.send_message(embed=e)
        except:
            self.bot.richConsole.print(
                f"[bold red][Queue Buttons][/] Error: {error}")
