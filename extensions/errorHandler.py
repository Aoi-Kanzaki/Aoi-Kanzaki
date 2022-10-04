import discord
from discord.ext import commands
from discord.app_commands import AppCommandError
from discord.app_commands.errors import CheckFailure, MissingPermissions, CommandOnCooldown, CommandInvokeError


class ErrorHandler(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        tree = self.bot.tree

        @tree.error
        async def on_app_command_error(interaction: discord.Interaction, error: AppCommandError):
            if isinstance(error, CommandOnCooldown):
                return await interaction.response.edit_message(
                    content=f"This command is on cooldown! You can try again in {round(error.retry_after)} seconds!"
                )
            elif isinstance(error, MissingPermissions):
                return await interaction.response.edit_message(
                    content=f"You don't have the required permissions to run this command!\nMissing Permissions: {error.missing_permissions}"
                )
            elif isinstance(error, CheckFailure):
                return await interaction.response.edit_message(
                    content="I have failed to match the required checks for you to use this command!"
                )
            elif isinstance(error, CommandInvokeError):
                e = discord.Embed(title="An Error has Occoured!")
                e.description = error
                e.colour = discord.Colour.red()
                return await interaction.response.edit_message(
                    embed=error.original
                )


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(ErrorHandler(bot))
