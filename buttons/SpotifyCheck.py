import discord


class Disconnect_Check(discord.ui.View):
    def __init__(self, bot, interaction) -> None:
        super().__init__(timeout=None)
        self.bot = bot
        self.db = self.bot.db.spotifyOauth

    @discord.ui.button(label="Yes", emoji="<:tickYes:697759553626046546>", style=discord.ButtonStyle.green)
    async def yes(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.db.find_one_and_delete({"_id": interaction.user.id})
        return await interaction.response.edit_message(
            content="Your spotify account has been disconnected!", view=None, embed=None)

    @discord.ui.button(label="No", emoji="<:tickNo:697759586538749982>", style=discord.ButtonStyle.red)
    async def no(self, interaction: discord.Interaction, button: discord.ui.Button):
        return await interaction.response.edit_message(
            content="Great, your account will stay connected!", view=None, embed=None)
