import discord
import aiohttp
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
        self.bot.logger.info(
            f"[Suggestion Modal] {interaction.user} has submitted a suggestion.")
        e = discord.Embed(
            colour=discord.Colour.teal()
        )
        e.add_field(name="Feature", value=self.feature.value, inline=False)
        e.add_field(name="Explanation",
                    value=self.explanation.value, inline=False)
        e.set_author(
            name=f"Suggestion from {interaction.user}", icon_url=interaction.user.avatar)
        e.set_footer(text=f"User ID: {interaction.user.id}")

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
        self.bot.logger.error(f"[Suggestion Modal] Error: {error}")
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
                f"[bold red][Suggest Modal][/] Error: {error}")
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(
                url=self.bot.config['webhooks']['mainlogs'], session=session)
            await webhook.send(embed=e)
