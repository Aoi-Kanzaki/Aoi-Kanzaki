import discord
from discord.ext import commands

from buttons.ModMailButtons import ModMailButtons


class ModMailModal(discord.ui.Modal):
    def __init__(self, bot: commands.AutoShardedBot):
        super().__init__(title="ModMail")
        self.bot = bot
        self.db = self.bot.db.modmail

        self.label = discord.ui.TextInput(
            label="Label:",
            placeholder="What's your issue?",
            required=True,
            max_length=100
        )
        self.add_item(self.label)

        self.description = discord.ui.TextInput(
            label="Description:",
            placeholder="Explain your issue in detail...",
            required=True,
            max_length=1800
        )
        self.add_item(self.description)

    async def on_submit(self, interaction: discord.Interaction):
        data = await self.db.find_one({"_id": interaction.guild.id})
        if not data:
            return await interaction.response.send_message(
                "This server doesn't have modmail setup!",
                ephemeral=True
            )

        channel = self.bot.get_channel(data["channel"])
        if not channel:
            return await interaction.response.send_message(
                "The modmail channel doesn't exist!",
                ephemeral=True
            )

        e = discord.Embed(
            colour=discord.Colour.teal(),
            title=f"ModMail from {interaction.user.name}"
        )
        e.add_field(name="Label:",
                    value=self.label.value, inline=False)
        e.add_field(name="Description:",
                    value=self.description.value, inline=False)
        e.set_thumbnail(url=interaction.user.avatar.url)
        e.set_footer(text=f"User ID: {interaction.user.id}")
        e.timestamp = interaction.created_at
        await channel.set_permissions(interaction.user, view_channel=True, send_messages=True)
        try:
            thread = await channel.create_thread(
                name=f"{interaction.user.name}'s ModMail",
                reason="ModMail Thread", type=discord.ChannelType.private_thread,
                auto_archive_duration=1440
            )
        except:
            thread = await channel.create_thread(
                name=f"{interaction.user.name}'s ModMail",
                reason="ModMail Thread", type=discord.ChannelType.public_thread,
                auto_archive_duration=1440
            )
        await thread.add_user(interaction.user)
        mods = [e for e in interaction.guild.members if "ModMail" in [
            r.name for r in e.roles]]
        for mod in mods:
            await thread.add_user(mod)
        await thread.send(f"Hey {interaction.user.mention}! Your message has been submitted! A mod will be with you shortly.")
        await thread.send(embed=e, view=ModMailButtons(self.bot))

        return await interaction.response.send_message(
            "Your message has been sent!",
            ephemeral=True
        )

    async def on_error(self, interaction: discord.Interaction, error: Exception) -> None:
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
                f"[bold red][ModMail Modal][/] Error: {error}")
