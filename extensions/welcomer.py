import discord
import aiohttp
from discord.ext import commands
from typing import Literal, Optional
from discord import app_commands as Aoi


class Welcomer(commands.GroupCog, description="Welcomer commands."):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db.welcomer

    @Aoi.command(name="toggle")
    @Aoi.checks.has_permissions(manage_guild=True)
    @Aoi.describe(toggle="Whether to enable or disable the welcomer.")
    async def toggle(self, interaction: discord.Interaction, toggle: Literal["enable", "disable"]):
        """Toggles the welcomer."""
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            data = {"_id": interaction.guild.id, "enabled": False,
                    "leave_message": "{user} has left!", "join_message": "Welcome {user} to {guild}!", "channel": None, "role": None}
            await self.db.insert_one(data)
        if toggle == "enable":
            if data["enabled"]:
                return await interaction.response.send_message("Welcomer is already enabled.", ephemeral=True)
            data["enabled"] = True
            await self.db.update_one({"_id": interaction.guild.id}, {"$set": data})
            return await interaction.response.send_message("Welcomer has been enabled.", ephemeral=True)
        if not data["enabled"]:
            return await interaction.response.send_message("Welcomer is already disabled.", ephemeral=True)
        data["enabled"] = False
        await self.db.update_one({"_id": interaction.guild.id}, {"$set": data})
        return await interaction.response.send_message("Welcomer has been disabled.", ephemeral=True)

    @Aoi.command(name="join-message")
    @Aoi.checks.has_permissions(manage_guild=True)
    @Aoi.describe(message="The message to send when a user joins.")
    async def joinmessage(self, interaction: discord.Interaction, message: Optional[str]):
        """Set the message to send when a user joins."""
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            data = {"_id": interaction.guild.id, "enabled": False,
                    "leave_message": "{user} has left!", "join_message": message, "channel": None, "role": None}
            await self.db.insert_one(data)
        if message is None:
            e = discord.Embed(title="Welcomer Message",
                              colour=discord.Colour.teal())
            e.description = "{user} = The user that joined.\n{guild} = The guild the user joined."
            e.add_field(name="Example",
                        value="Welcome {user} to {guild}!", inline=False)
            e.add_field(name="Current", value=data["join_message"])
            return await interaction.response.send_message(embed=e, ephemeral=True)
        data["join_message"] = message
        await self.db.update_one({"_id": interaction.guild.id}, {"$set": data})
        return await interaction.response.send_message("Welcomer message has been set.", ephemeral=True)

    @Aoi.command(name="leave-message")
    @Aoi.checks.has_permissions(manage_guild=True)
    @Aoi.describe(message="The message to send when a user leaves.")
    async def leavemessage(self, interaction: discord.Interaction, message: Optional[str]):
        """Set the message to send when a user leaves."""
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            data = {"_id": interaction.guild.id, "enabled": False,
                    "leave_message": message, "join_message": "Welcome {user} to {guild}!", "channel": None, "role": None}
            await self.db.insert_one(data)
        if message is None:
            e = discord.Embed(title="Welcomer Message",
                              colour=discord.Colour.teal())
            e.description = "{user} = The user that left.\n{guild} = The guild the user left."
            e.add_field(name="Example",
                        value="{user} has left!", inline=False)
            e.add_field(name="Current", value=data["leave_message"])
            return await interaction.response.send_message(embed=e, ephemeral=True)
        data["leave_message"] = message
        await self.db.update_one({"_id": interaction.guild.id}, {"$set": data})
        return await interaction.response.send_message("Welcomer message has been set.", ephemeral=True)

    @Aoi.command(name="channel")
    @Aoi.checks.has_permissions(manage_guild=True)
    @Aoi.describe(channel="The channel to send the welcomer message in.")
    async def channel(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel]):
        """Set the channel to send the welcomer message in."""
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            data = {"_id": interaction.guild.id, "enabled": False,
                    "leave_message": "{user} has left!", "join_message": "Welcome {user} to {guild}!", "channel": channel.id, "role": None}
            await self.db.insert_one(data)
        if channel is None:
            data["channel"] = None
            await self.db.update_one({"_id": interaction.guild.id}, {"$set": data})
            return await interaction.response.send_message("Welcomer channel has disabled.", ephemeral=True)
        data["channel"] = channel.id
        await self.db.update_one({"_id": interaction.guild.id}, {"$set": data})
        return await interaction.response.send_message("Welcomer channel has been set.", ephemeral=True)

    @Aoi.command(name="role")
    @Aoi.checks.has_permissions(manage_guild=True)
    @Aoi.describe(role="The role to give to the user when they join.")
    async def role(self, interaction: discord.Interaction, role: Optional[discord.Role]):
        """Set the role to give to the user when they join."""
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            data = {"_id": interaction.guild.id, "enabled": False,
                    "leave_message": "{user} has left!", "join_message": "Welcome {user} to {guild}!", "channel": None, "role": role.id}
            await self.db.insert_one(data)
        if role is None:
            data["role"] = None
            await self.db.update_one({"_id": interaction.guild.id}, {"$set": data})
            return await interaction.response.send_message("Welcomer role has been removed.", ephemeral=True)
        data["role"] = role.id
        await self.db.update_one({"_id": interaction.guild.id}, {"$set": data})
        return await interaction.response.send_message("Welcomer role has been set.", ephemeral=True)

    @Aoi.command(name="config")
    @Aoi.checks.has_permissions(manage_guild=True)
    async def config(self, interaction: discord.Interaction):
        """View the current welcomer config."""
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            return await interaction.response.send_message("Welcomer is not configured.", ephemeral=True)
        embed = discord.Embed(title="Welcomer Configuration",
                              color=discord.Color.teal())
        embed.add_field(name="Toggle", value=(
            "Enabled." if data["enabled"] else "Disabled."))
        embed.add_field(name="Channel", value=(interaction.guild.get_channel(
            data["channel"]).mention if data["channel"] is not None else "Disabled."))
        embed.add_field(
            name="Role", value=(interaction.guild.get_role(data["role"]).mention if data["role"] is not None else "Disabled."))
        embed.add_field(name="Join Messsage", value=data["join_message"].format(
            user=interaction.user.mention, guild=interaction.guild.name), inline=False)
        embed.add_field(name="Leave Message", value=data["leave_message"].format(
            user=interaction.user.mention, guild=interaction.guild.name), inline=False)
        return await interaction.response.send_message(embed=embed, ephemeral=True)

    @config.error
    @toggle.error
    @role.error
    @channel.error
    @joinmessage.error
    @leavemessage.error
    async def send_error(self, interaction: discord.Interaction, error):
        self.bot.logger.error(f"[Welcomer] Error: {error}")
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
            async with aiohttp.ClientSession() as session:
                webhook = discord.Webhook.from_url(
                    url=self.bot.config['webhooks']['mainlogs'], session=session)
                await webhook.send(embed=e)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        data = await self.db.find_one({"_id": member.guild.id})
        if data:
            if data["enabled"]:
                if data["channel"] is not None:
                    channel = member.guild.get_channel(data["channel"])
                    if channel is not None:
                        try:
                            await channel.send(data["join_message"].format(user=member.mention, guild=member.guild.name))
                        except discord.Forbidden:
                            pass
                if data["role"] is not None:
                    role = member.guild.get_role(data["role"])
                    if role is not None:
                        try:
                            await member.add_roles(role)
                        except discord.Forbidden:
                            pass

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        data = await self.db.find_one({"_id": member.guild.id})
        if data:
            if data["enabled"]:
                if data["channel"] is not None:
                    channel = member.guild.get_channel(data["channel"])
                    if channel is not None:
                        try:
                            await channel.send(data["leave_message"].format(user=member.mention, guild=member.guild.name))
                        except discord.Forbidden:
                            pass


async def setup(bot):
    await bot.add_cog(Welcomer(bot))
