import discord
from discord.ext import commands


class BugReport(discord.ui.Modal):
    def __init__(self, bot: commands.AutoShardedBot):
        super().__init__(title="Submit a Bug Report:")
        self.bot = bot

        self.bug = discord.ui.TextInput(
            label="What's the bug you're reporting?",
            placeholder="Explain the bug in detail..",
            required=True,
            max_length=1800
        )
        self.add_item(self.bug)

        self.replicate = discord.ui.TextInput(
            label="How would Jonny replicate this bug?",
            placeholder="Explain the steps and commands you used to get this bug.",
            required=True,
            max_length=1800
        )
        self.add_item(self.replicate)

    async def on_submit(self, interaction: discord.Interaction):
        e = discord.Embed(
            title=f"Bug Report from {interaction.user.name}"
        )
        e.add_field(name="Bug:", value=self.bug.value, inline=False)
        e.add_field(name="How to Replicate:",
                    value=self.replicate.value, inline=False)

        for devID in interaction.client.config['slashCommands']['devIDS']:
            dev = await self.bot.fetch_user(devID)
            await dev.send(embed=e)
        await interaction.response.send_message(f'Thanks for your submitting your bug!', ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        self.bot.richConsole.print(
            "[bold red][Bug Report][/] [red]Error: [white]" + str(error))
        await interaction.response.send_message('Oops! Something went wrong.', ephemeral=True)
