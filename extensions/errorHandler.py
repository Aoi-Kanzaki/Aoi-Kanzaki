import discord
import traceback
from discord.ext import commands
from discord.app_commands import AppCommandError
from discord.app_commands.errors import CheckFailure, MissingPermissions, CommandOnCooldown, CommandInvokeError


class ErrorHandler(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        bot.tree.on_error = self.on_app_command_error

    async def on_app_command_error(self, interaction: discord.Interaction, error: AppCommandError):
        if isinstance(error, CommandOnCooldown):
            return await interaction.response.send_message(
                content=f"This command is on cooldown! You can try again in {round(error.retry_after)} seconds!",
                ephemeral=True
            )
        elif isinstance(error, MissingPermissions):
            return await interaction.response.send_message(
                content=f"You don't have the required permissions to run this command!\nMissing Permissions: {error.missing_permissions}",
                ephemeral=True
            )
        elif isinstance(error, CheckFailure):
            return await interaction.response.send_message(
                content="I have failed to match the required checks for you to use this command!",
                ephemeral=True
            )
        elif isinstance(error, CommandInvokeError):
            try:
                em = discord.Embed(title="An Error has Occoured!")
                em.description = f"{traceback.format_exc(limit=0, chain=False)}"
                em.colour = discord.Colour.red()
                return await interaction.response.send_message(
                    embed=em,
                    ephemeral=True
                )
            except Exception as e:
                print(e)
        elif isinstance(error, AttributeError):
            em = discord.Embed(colour=discord.Colour.red())
            em.title = "Oh no, an Attribute Error!"
            em.description = f"{traceback.format_exc(limit=0, chain=False)}"
            return await interaction.response.send_message(
                embed=em,
                ephemeral=True
            )
        else:
            return await interaction.response.send_message(
                content=f"An Error Has Occoured!\n{error}",
                ephemeral=True
            )


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(ErrorHandler(bot))
