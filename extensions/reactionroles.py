import discord
import typing
import emojis
from discord.ext import commands
from discord import app_commands as Aoi


class ReactionRolesNotSetup(commands.CommandError):
    """Reaction roles are not setup for this guild."""
    pass


def is_setup():
    async def wrap_func(interaction: discord.Interaction):
        data = interaction.client.db.find_one({"_id": interaction.guild.id})
        if data is None:
            raise ReactionRolesNotSetup
        if data["message_id"] is None:
            raise ReactionRolesNotSetup
        return True
    return Aoi.check(wrap_func)


class UpdateEmbed(discord.ui.View):
    def __init__(self, bot: commands.AutoShardedBot, data: dict):
        super().__init__(timeout=None)
        self.bot = bot
        self.data = data
        self.db = self.bot.db.reactionroles

    @discord.ui.button(label="Update Embed", style=discord.ButtonStyle.green)
    async def update_embed(self, interaction: discord.Interaction, button: discord.ui.Button):
        data = await self.db.find_one({"_id": interaction.guild.id})
        e = discord.Embed(
            colour=discord.Colour.blurple(), title="Reaction Roles")
        e.set_thumbnail(url=interaction.guild.icon.url)

        e.description = ""
        for rr in data["roles"]:
            role = interaction.guild.get_role(rr["role"])
            e.description += f"{rr['emoji']} - {role.mention}\n"
        try:
            if data["message_id"] is None:
                return await interaction.response.edit_message(
                    content="Please update using the command `/reactionroles channel`.", view=None)
            if data["channel_id"] is None:
                return await interaction.response.edit_message(
                    content="Please update using the command `/reactionroles channel`.", view=None)
            channel = interaction.guild.get_channel(data["channel_id"])
            try:
                message = await channel.fetch_message(data["message_id"])
                if message is not None:
                    await message.delete()
            except:
                pass
            msg = await channel.send(embed=e)
            for rr in self.data["roles"]:
                await msg.add_reaction(rr["emoji"])
            await self.db.update_one({"_id": interaction.guild.id}, {
                "$set": {"message_id": msg.id}})
            return await interaction.response.send_message(
                content="Successfully updated the embed!", view=None)
        except:
            return await interaction.followup.send("Please set a channel first! Use the command `/reactionrole channel`.")

    @discord.ui.button(label="Later", style=discord.ButtonStyle.grey)
    async def later(self, interaction: discord.Interaction, button: discord.ui.Button, ):
        await interaction.response.defer()
        await interaction.response.edit_message(
            content="You can update the embed later! Just use the `/reactionroles channel` command!", view=None)


class ReactionRoles(commands.GroupCog, description="Reaction roles for your server."):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.db = self.bot.db.reactionroles

    @Aoi.command(name="channel", description="Set the channel for reaction roles")
    @Aoi.describe(channel="The channel to set the reaction roles in")
    @commands.has_permissions(manage_guild=True)
    async def channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        await interaction.response.defer(ephemeral=True)
        try:
            await channel.send("This is a test message for reaction roles.", delete_after=0.05)
        except discord.Forbidden:
            return await interaction.followup.send("I do not have permissions to send messages in that channel.")

        e = discord.Embed(title="Reaction Roles",
                          color=discord.Color.blurple())
        e.set_thumbnail(url=interaction.guild.icon.url)
        e.description = ""
        data = await self.db.find_one({"_id": interaction.guild.id})
        for rr in data["roles"]:
            role = interaction.guild.get_role(rr['role'])
            e.description += f"{rr['emoji']} {role.mention}\n"

        m = await channel.send(embed=e)
        for rr in data["roles"]:
            await m.add_reaction(rr["emoji"])
        if data['message_id'] is not None:
            old = await channel.fetch_message(data['message_id'])
            await old.delete()
        await self.db.update_one({"_id": interaction.guild.id}, {"$set": {"message_id": m.id}})
        await self.db.update_one({"_id": interaction.guild.id}, {"$set": {"channel_id": channel.id}})
        await interaction.followup.send("Successfully set the reaction roles channel.")

    @Aoi.command(name="add", description="Add a reaction role")
    @Aoi.describe(role="The role to add", emoji="The emoji to add")
    @commands.has_permissions(manage_guild=True)
    async def add(self, interaction: discord.Interaction, role: discord.Role, emoji: str):
        if isinstance(emoji, discord.Emoji):
            emoji = emoji.id
        else:
            emoji = emojis.encode(emoji)
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            data = {"_id": interaction.guild.id,
                    "message_id": None, "roles": []}
            await self.db.insert_one(data)
        data["roles"].append({"role": role.id, "emoji": emoji})
        await self.db.update_one({"_id": interaction.guild.id}, {"$set": {"roles": data["roles"]}})
        await interaction.response.send_message(
            f"Successfully added {role.mention} with {emoji} to reaction roles.\n"
            "Should I update the embed? Or do you want to use the `/reactionrole channel` command later?",
            ephemeral=True,
            view=UpdateEmbed(self.bot, data)
        )

    @Aoi.command(name="remove", description="Remove a reaction role")
    @Aoi.describe(role="The role to remove")
    @commands.has_permissions(manage_guild=True)
    async def remove(self, interaction: discord.Interaction, role: discord.Role):
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            return await interaction.response.send_message("There are no reaction roles setup for this guild.", ephemeral=True)
        data["roles"] = [rr for rr in data["roles"] if rr["role"] != role.id]
        await self.db.update_one({"_id": interaction.guild.id}, {"$set": {"roles": data["roles"]}})
        await interaction.response.send_message(
            f"Successfully removed {role.mention} from reaction roles.\n"
            "Should I update the embed? Or do you want to use the `/reactionrole channel` command later?",
            ephemeral=True,
            view=UpdateEmbed(self.bot, (await self.db.find_one({"_id": interaction.guild.id})))
        )

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
