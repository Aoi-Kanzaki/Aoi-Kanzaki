import discord
from discord import app_commands as Fresh


def is_dev():
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id in interaction.client.config['slashCommands']['devIDS']
    return Fresh.check(predicate)
