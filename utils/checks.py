import discord
from discord import app_commands as Aoi


def is_dev():
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id in interaction.client.config['slashCommands']['devIDS']
    return Aoi.check(predicate)
