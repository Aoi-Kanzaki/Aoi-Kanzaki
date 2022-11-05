import discord
import typing
from discord.ext import commands
from discord import app_commands as Aoi

from modals.ModMailModal import ModMailModal
from buttons.ModMailButtons import ModMailButtons, EnsureClose


class ModMail(commands.GroupCog, description="ModMail commands."):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.db = self.bot.db.modmail
        self.bot.add_view(ModMailButtons(self.bot))

    @Aoi.command(name="send", description="Send a message to the server mods.")
    async def send(self, interaction: discord.Interaction):
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            return await interaction.response.send_message("This server does not have modmail setup.")
        elif data["enabled"] is False:
            return await interaction.response.send_message("This server does not have modmail setup.")

        await interaction.response.send_modal(ModMailModal(self.bot))

    @Aoi.command(name="close", description="Close a modmail thread.")
    async def close(self, interaction: discord.Interaction):
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            return await interaction.response.send_message("This server does not have modmail setup.")
        elif data["enabled"] is False:
            return await interaction.response.send_message("This server does not have modmail setup.")

        channel = self.bot.get_channel(data["channel"])
        thread = interaction.channel
        mods = [e.id for e in interaction.guild.members if "ModMail" in [
            r.name for r in e.roles]]
        members = [e for e in thread.members if e.id not in mods]

        if interaction.user.id not in mods:
            return await interaction.response.send_message(
                "You don't have permission to close this thread!",
                ephemeral=True
            )
        return await interaction.response.send_message(
            embed=discord.Embed(
                description="Are you sure you want to close this thread?",
                color=discord.Color.red(),
            ),
            view=EnsureClose(self.bot, thread, channel,
                             interaction.user, mods, members),
            ephemeral=True
        )

    @Aoi.command(name="setup", description="Setup modmail for the server.")
    @Aoi.describe(toggle="Whether to enable or disable ModMail.")
    async def setup(self, interaction: discord.Interaction, toggle: typing.Literal["enable", "disable"]):
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is not None:
            if toggle == "enable":
                if data["enabled"] is True:
                    return await interaction.response.send_message("Modmail is already enabled for this server.")
                return await interaction.response.send_message("Modmail is already setup for this server.")
            try:
                channel = await interaction.guild.fetch_channel(data['channel'])
                await channel.delete()
                role = interaction.guild.get_role(data['role'])
                await role.delete()
            except (discord.Forbidden, discord.HTTPException, discord.NotFound):
                pass
            await self.db.delete_one({"_id": interaction.guild.id})
            return await interaction.response.send_message("Modmail has been disabled for this server.")
        else:
            if toggle == "enable":
                channel = await interaction.guild.create_text_channel("modmail", reason="Modmail setup.", topic="Modmail channel.")
                role = await interaction.guild.create_role(name="ModMail", reason="Modmail setup.")
                await channel.set_permissions(role, send_messages=True, read_messages=True)
                await channel.set_permissions(interaction.guild.default_role, send_messages=False, read_messages=False)
                await interaction.user.add_roles(role, reason="Modmail setup.")
                embed = discord.Embed(title="ModMail Setup",
                                      description="ModMail has been setup for this server.\n"
                                      "You can now send messages to the mods using `/mod-mail send`.\n"
                                      "You can disable modmail using `/mod-mail setup disable`.\n"
                                      f"You can now give mods the {role.mention} role for pings.\n",
                                      color=discord.Color.teal())
                await channel.send(embed=embed, content=f"{role.mention} ModMail Setup")
                await self.db.insert_one({"_id": interaction.guild.id, "enabled": True, "channel": channel.id, "role": role.id})
                return await interaction.response.send_message("Modmail has been enabled for this server.")
            return await interaction.response.send_message("Modmail is not setup for this server.")

    @setup.error
    @close.error
    @send.error
    async def send_error(self, interaction: discord.Interaction, error):
        e = discord.Embed(title="An Error has Occurred!",
                          colour=discord.Colour.red())
        e.add_field(name="Error:", value=error)
        try:
            await interaction.response.send_message(embed=e)
        except:
            await interaction.followup.send(embed=e)


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(ModMail(bot))
