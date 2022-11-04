import discord
from discord.ext import commands


class ModMailButtons(discord.ui.View):
    def __init__(self, bot: commands.AutoShardedBot):
        super().__init__(timeout=None)
        self.bot = bot
        self.db = self.bot.db.modmail

    @discord.ui.button(label="Close", custom_id="Close Modmail", style=discord.ButtonStyle.danger)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = await self.db.find_one({"_id": interaction.guild.id})
        if not data:
            return await interaction.response.send_message(
                "This server doesn't have modmail setup!",
                ephemeral=True
            )
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
                color=discord.Color.red()
            ),
            view=EnsureClose(self.bot, thread, channel,
                             interaction.user, mods, members),
            ephemeral=True
        )


class EnsureClose(discord.ui.View):
    def __init__(self, bot: commands.AutoShardedBot, thread, channel, user, mods, members):
        super().__init__(timeout=None)
        self.bot = bot
        self.thread = thread
        self.channel = channel
        self.user = user
        self.mods = mods
        self.members = members
        self.db = self.bot.db.modmail

    @discord.ui.button(label="Yes", style=discord.ButtonStyle.success)
    async def close(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = await self.db.find_one({"_id": interaction.guild.id})
        if not data:
            return await interaction.response.send_message(
                "This server doesn't have modmail setup!",
                ephemeral=True
            )

        if self.user.id not in self.mods:
            return await interaction.response.send_message(
                "You don't have permission to close this thread!",
                ephemeral=True
            )
        await self.thread.delete()
        for member in self.members:
            member = self.channel.guild.get_member(member.id)
            await self.channel.set_permissions(member, view_channel=False, send_messages=False)
        await interaction.response.send_message(
            "This thread has been closed!", ephemeral=True)

    @discord.ui.button(label="Cancel", custom_id="Cancel", style=discord.ButtonStyle.secondary)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(
            "This thread will not be closed.",
            ephemeral=True
        )
        self.stop()
