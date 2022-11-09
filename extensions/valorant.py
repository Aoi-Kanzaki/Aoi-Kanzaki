import discord
from utils.valUtils import Region
from discord.ext import commands
from discord import app_commands as Aoi


class Valorant(commands.GroupCog, description="Crypto related commands."):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    @Aoi.command(name="status")
    @Aoi.describe(region="The region you want to check the status of.")
    async def status(self, interaction: discord.Interaction, region: str):
        """Check Valorant's servers."""
        region = Region(region)
        if region.get_status_issue() == False:
            await interaction.response.send_message("All servers are running just fine!")
        else:
            if region.incident_check() == True:
                global embed1
                embed1 = discord.Embed(
                    colour=discord.Colour.orange(),
                    title=region.incidents_title()
                )
                embed1.add_field(name=region.incidents_date(),
                                 value=region.incidents_reason())
                return await interaction.response.send_message(
                    embed=embed1,
                )
            if region.maintenence_check() == True:
                embed2 = discord.Embed(
                    colour=discord.Colour.orange(),
                    title=region.maintenances_title()
                )
                embed2.add_field(name=region.incidents_reason(),
                                 value=region.maintenances_reason())
                return await interaction.response.send_message(
                    embed=embed2,
                )

    @status.error
    async def send_error(self, interaction: discord.Interaction, error):
        self.bot.logger.error(f"[Valorant] Error: {error}")
        if isinstance(error, commands.MissingPermissions):
            return await interaction.response.send_message("You do not have the required permissions to use this command!", ephemeral=True)
        if isinstance(error, commands.MissingRequiredArgument):
            return await interaction.response.send_message("You are missing a required argument!", ephemeral=True)
        if isinstance(error, commands.BadArgument):
            return await interaction.response.send_message("You provided an invalid argument!", ephemeral=True)
        if isinstance(error, commands.CommandInvokeError):
            return await interaction.response.send_message("An error occurred while running this command!", ephemeral=True)
        else:
            e = discord.Embed(title="An Error has Occurred!",
                              colour=discord.Colour.red())
            e.add_field(name="Error:", value=error)
            try:
                await interaction.response.send_message(embed=e)
            except:
                await interaction.followup.send(embed=e)


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(Valorant(bot))
