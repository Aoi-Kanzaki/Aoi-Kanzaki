import discord


class EnsureChoiceButtons(discord.ui.View):
    def __init__(self, bot, uri) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.song = uri

    @discord.ui.button(label="Yes", emoji="<:tickYes:697759553626046546>", style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = await self.bot.db.favorites.find_one({"_id": interaction.user.id})
        if self.song in data['songs']:
            await self.bot.db.favorites.update_one({"_id": interaction.user.id}, {
                "$pull": {"songs": self.song}})
            return await interaction.response.edit_message(
                content="<:tickYes:697759553626046546> I have removed the song from your favorites!", embed=None, view=None)
        else:
            return await interaction.response.edit_message(
                content="<:tickNo:697759586538749982> There must be an issue because I don't see this song in your favorites!",
                view=None, embed=None)

    @discord.ui.button(label="No", emoji="<:tickNo:697759586538749982>", style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        return await interaction.response.edit_message(
            content="Great, the song will stay!", view=None, embed=None)
