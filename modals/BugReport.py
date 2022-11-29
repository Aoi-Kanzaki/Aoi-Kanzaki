import discord
import aiohttp
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
        e = discord.Embed(colour=discord.Colour.teal())
        e.set_author(
            name=f"Bug Report from {interaction.user}", icon_url=interaction.user.avatar)
        e.add_field(name="Bug:", value=self.bug.value, inline=False)
        e.add_field(name="How to Replicate:",
                    value=self.replicate.value, inline=False)
        e.set_footer(text=f"User ID: {interaction.user.id}")
        for devID in interaction.client.config['slashCommands']['devIDS']:
            dev = await self.bot.fetch_user(devID)
            await dev.send(embed=e)
        await interaction.response.send_message(f'Thanks for your submitting your bug!', ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
        self.bot.logger.error(f"[Bug Report Modal] Error: {error}")
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
                f"[bold red][Bug Report Modal][/] Error: {error}")
        async with aiohttp.ClientSession() as session:
            webhook = discord.Webhook.from_url(
                url=self.bot.config['webhooks']['mainlogs'], session=session)
            await webhook.send(embed=e)
