import discord
import typing
import emojis
from discord.ext import commands
from discord import app_commands as Aoi
from utils.checks import is_setup


class ReactionRoles(commands.GroupCog, description="Reaction roles for your server."):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.db = self.bot.db.reactionroles

    @Aoi.command(name="update", description="Update the embed for reaction roles.")
    @Aoi.checks.has_permissions(manage_guild=True)
    @is_setup()
    async def update(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        data = await self.db.find_one({"_id": interaction.guild.id})
        message = await interaction.channel.fetch_message(data["message_id"])
        if message is None:
            return await interaction.response.send_message(
                "Reaction roles are not setup for this guild.",
                ephemeral=True
            )
        else:
            await message.delete()

        e = discord.Embed(colour=discord.Colour.teal())
        e.set_author(name="Reaction Roles", icon_url=interaction.guild.icon)
        e.description = "React to this message to get a role!\n"
        for rr in data["roles"]:
            role = interaction.guild.get_role(rr['role'])
            if role is None:
                continue
            else:
                e.description += f"{rr['emoji']} - {role.mention}\n"

        channel = interaction.guild.get_channel(data["channel_id"])
        if channel is None:
            return await interaction.response.send_message(
                "Reaction roles are not setup for this guild.",
                ephemeral=True
            )

        msg = await channel.send(embed=e)
        for rr in data["roles"]:
            await msg.add_reaction(rr["emoji"])

        await self.db.update_one({"_id": interaction.guild.id}, {"$set": {"message_id": msg.id}})
        await interaction.followup.send("Updated reaction roles message!")

    @Aoi.command(name="setup", description="Setup reaction roles for your server.")
    @Aoi.describe(
        channel="The channel to send the reaction roles message in.",
        role="The role to give when a user reacts to the message.",
        emoji="The emoji to react with."
    )
    @Aoi.checks.has_permissions(manage_guild=True)
    async def setup(self, interaction: discord.Interaction, channel: discord.TextChannel, role: discord.Role, emoji: str):
        await interaction.response.defer(ephemeral=True, thinking=True)
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            emoji = emojis.encode(emoji)

            e = discord.Embed(colour=discord.Colour.teal())
            e.set_author(name="Reaction Roles",
                         icon_url=interaction.guild.icon)
            e.description = f"React to this message to get a role!\n{emoji} - {role.mention}\n"

            msg = await channel.send(embed=e)
            await msg.add_reaction(emoji)

            await self.db.insert_one(
                {"_id": interaction.guild.id, "message_id": msg.id,
                 "channel_id": channel.id, "roles": [{"role": role.id, "emoji": emoji}]})
            await interaction.followup.send("Setup reaction roles!")
        else:
            await interaction.followup.send("Reaction roles are already setup for this server!")

    @Aoi.command(name="add", description="Add a reaction role to the list.")
    @Aoi.describe(
        role="The role to give when the user reacts.",
        emoji="The emoji to react with."
    )
    @Aoi.checks.has_permissions(manage_guild=True)
    @is_setup()
    async def add(self, interaction: discord.Interaction, role: discord.Role, emoji: str):
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            return await interaction.response.send_message(
                "Reaction roles are not setup for this guild.",
                ephemeral=True
            )
        emoji = emojis.encode(emoji)

        await self.db.update_one({"_id": interaction.guild.id}, {"$push": {"roles": {"role": role.id, "emoji": emoji}}})
        await interaction.response.send_message(f"Added {role.mention} to the reaction roles list!\n"
                                                "Please run the update command to update the message!", ephemeral=True)

    @Aoi.command(name="remove", description="Remove a reaction role from the list.")
    @is_setup()
    @Aoi.checks.has_permissions(manage_guild=True)
    async def remove(self, interaction: discord.Interaction, role: discord.Role):
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            return await interaction.response.send_message(
                "Reaction roles are not setup for this guild.",
                ephemeral=True
            )

        await self.db.update_one({"_id": interaction.guild.id}, {"$pull": {"roles": {"role": role.id}}})
        await interaction.response.send_message(f"Removed {role.mention} from the reaction roles list!\n"
                                                "Please run the update command to update the message!", ephemeral=True)

    @Aoi.command(name="disable", description="Disable reaction roles for your server.")
    @Aoi.checks.has_permissions(manage_guild=True)
    @is_setup()
    async def disable(self, interaction: discord.Interaction):
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            return await interaction.response.send_message(
                "Reaction roles are not setup for this guild.",
                ephemeral=True
            )

        message = await interaction.channel.fetch_message(data["message_id"])
        if message is None:
            return await interaction.response.send_message(
                "Reaction roles are not setup for this guild.",
                ephemeral=True
            )
        else:
            await message.delete()

        await self.db.delete_one({"_id": interaction.guild.id})
        await interaction.response.send_message("Disabled reaction roles!", ephemeral=True)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.member.bot:
            return
        data = await self.db.find_one({"_id": payload.guild_id})
        if data is None or data["message_id"] is None:
            return
        if data["message_id"] != payload.message_id:
            return
        for rr in data["roles"]:
            if rr["emoji"] == str(payload.emoji):
                role = payload.member.guild.get_role(rr["role"])
                await payload.member.add_roles(role)

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        data = await self.db.find_one({"_id": payload.guild_id})
        member = payload.member
        guild = self.bot.get_guild(payload.guild_id)
        if member is None:
            member = await guild.fetch_member(payload.user_id)
        if guild is None or member.bot:
            return
        if data is None or data["message_id"] is None:
            return
        if data["message_id"] != payload.message_id:
            return
        for rr in data["roles"]:
            if rr["emoji"] == str(payload.emoji):
                role = guild.get_role(rr["role"])
                await member.remove_roles(role)


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(ReactionRoles(bot))
