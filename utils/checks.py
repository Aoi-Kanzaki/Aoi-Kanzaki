import discord
from discord import app_commands as Aoi


def is_dev():
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.id in interaction.client.config['slashCommands']['devIDS']
    return Aoi.check(predicate)


def is_setup():
    async def wrap_func(interaction: discord.Interaction):
        async def send_message():
            return await interaction.response.send_message(
                "Reaction roles are not setup for this guild.",
                ephemeral=True
            )
        data = await interaction.client.db.reactionroles.find_one(
            {"_id": interaction.guild.id})
        if data is None:
            return await send_message()
        try:
            if data["message_id"] is None:
                return await send_message()
            if data["roles"] is None:
                return await send_message()
        except KeyError:
            return await send_message()
        return True
    return Aoi.check(wrap_func)
