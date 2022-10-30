import discord
from discord.ext import commands


class Suggest(discord.ui.Modal):
    def __init__(self, bot: commands.AutoShardedBot):
        super().__init__(title="Submit a Suggestion:")
        self.bot = bot

        self.feature = discord.ui.TextInput(
            label="What is the name of the feature?",
            placeholder="What is this feature called..?",
            required=True,
            max_length=100
        )
        self.add_item(self.feature)

        self.explanation = discord.ui.TextInput(
            label="Describe in full detail about the feature.",
            placeholder="Explain what the feature should do here...",
            required=True,
            max_length=1800
        )
        self.add_item(self.explanation)

    async def on_submit(self, interaction: discord.Interaction):
        e = discord.Embed(
            colour=discord.Colour.teal(),
            title=f"Suggestion from {interaction.user.name}"
        )
        e.add_field(name="Feature name:",
                    value=self.feature.value, inline=False)
        e.add_field(name="Description:",
                    value=self.explanation.value, inline=False)

        guild = await self.bot.fetch_guild(678226695190347797)
        channel = await guild.fetch_channel(1036098613220229130)

        msg = await channel.send(embed=e)

        reactions = ['<:tickYes:697759553626046546>',
                     '<:tickNo:697759586538749982>']
        for reaction in reactions:
            await msg.add_reaction(reaction)

        if interaction.guild.id == 678226695190347797:
            return await interaction.response.send_message(
                'Thanks for submitting your suggestion! You should be able to see it in <#1036098613220229130>!',
                ephemeral=True
            )
        else:
            return await interaction.response.send_message(
                'Thanks for submitting your suggestion! You should be able to see it in <#1036098613220229130> now in the support server!',
                ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)
