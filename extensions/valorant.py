import discord
from utils.valUtils import Region
from discord.ext import commands
from discord import app_commands as Fresh


class Valorant(commands.GroupCog, name="valorant", description="Crypto related commands."):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    @Fresh.command(name="status")
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


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(Valorant(bot))
