import discord
from datetime import datetime
from discord.ext import commands
from discord import app_commands as Aoi


class ModLog(commands.GroupCog, description="All ModLog related commands."):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.db = self.bot.db.ModLog

    @Aoi.command(name="enable")
    @Aoi.checks.has_permissions(administrator=True)
    async def enable(self, interaction: discord.Interaction):
        """Enable the modlog for the server."""
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            await self.db.insert_one({"_id": interaction.guild.id})
            channel = await interaction.guild.create_text_channel("modlog")
            await self.db.update_one({"_id": interaction.guild.id}, {
                "$set": {"enabled": True}})
            await self.db.update_one({"_id": interaction.guild.id}, {
                "$set": {"channel": channel.id}})
            return await interaction.response.send_message(
                content=f"ModLog has been enabled! Logs will be sent to {channel.mention}"
            )
        else:
            if data['enabled'] is True:
                return await interaction.response.send_message(
                    "<:tickNo:697759586538749982> ModLog is already enabled!")
            else:
                if data['channel'] is None:
                    channel = await interaction.guild.create_text_channel("modlog")
                    await self.db.update_one({"_id": interaction.guild.id}, {
                        "$set": {"enabled": True}})
                    await self.db.update_one({"_id": interaction.guild.id}, {
                        "$set": {"channel": channel.id}})
                    return await interaction.response.send_message(
                        content=f"ModLog has been enabled! Logs will be sent to {channel.mention}"
                    )
                await self.db.update_one({"_id": interaction.guild.id}, {
                    "$set": {"enabled": True}})
                return await interaction.response.send_message(
                    "<:tickYes:697759553626046546> ModLog has been enabled!")

    @Aoi.command(name="disable")
    @Aoi.checks.has_permissions(administrator=True)
    async def disable(self, interaction: discord.Interaction):
        """Disable modlog for this server."""
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            return await interaction.response.send_message(
                "<:tickNo:697759586538749982> ModLog is not enabled!")
        else:
            if data['enabled'] is False:
                return await interaction.response.send_message(
                    "<:tickNo:697759586538749982> ModLog is not enabled!")
            else:
                channel = self.bot.get_channel(data['channel'])
                try:
                    await channel.delete()
                    await self.db.update_one({"_id": interaction.guild.id}, {
                        "$set": {"channel": None}})
                except (discord.Forbidden, discord.NotFound, AttributeError):
                    await self.db.update_one({"_id": interaction.guild.id}, {
                        "$set": {"channel": None}})
                await self.db.update_one({"_id": interaction.guild.id}, {
                    "$set": {"enabled": False}})
                return await interaction.response.send_message(
                    "<:tickYes:697759553626046546> ModLog has been disabled!")

    @enable.error
    @disable.error
    async def send_error(self, interaction: discord.Interaction, error):
        self.bot.logger.error(f"[ModLog] Error: {error}")
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

    @commands.Cog.listener()
    async def on_message_edit(self, message: discord.Message, new_message: discord.Message):
        if message.author.bot:
            return
        data = await self.db.find_one({"_id": message.guild.id})
        if data is None:
            return
        if data['enabled'] is True:
            channel = self.bot.get_channel(data['channel'])
            e = discord.Embed(colour=0xf58142, timestamp=datetime.utcnow())
            e.set_author(name=message.author,
                         icon_url=message.author.avatar.url)
            e.description = (f"**Messaged Edited in {message.channel.mention}**\n"
                             f"**Before:** {message.content}\n"
                             f"**After:** {new_message.content}")
            e.set_thumbnail(url=message.author.avatar.url)
            e.set_footer(text=f"Message ID: {message.id}")
            return await channel.send(embed=e)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return
        data = await self.db.find_one({"_id": message.guild.id})
        if data is None:
            return
        if data['enabled'] is True:
            channel = self.bot.get_channel(data['channel'])
            e = discord.Embed(colour=0xf55742, timestamp=datetime.utcnow())
            e.set_author(name=message.author,
                         icon_url=message.author.avatar.url)
            e.description = (f"**Message deleted in {message.channel.mention}**\n"
                             f"{message.content}")
            e.set_thumbnail(url=message.author.avatar.url)
            e.set_footer(text=f"Message ID: {message.id}")
            return await channel.send(embed=e)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.bot:
            return
        data = await self.db.find_one({"_id": member.guild.id})
        if data is None:
            return
        else:
            if data['enabled'] is True:
                channel = self.bot.get_channel(data['channel'])
                embed = discord.Embed(
                    title="Member Joined",
                    description=f"**Member:** {member.mention}\n"
                    f"**Account Created:** {member.created_at.strftime('%B %d %Y')}",
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=member.avatar)
                embed.set_footer(
                    text=f"Member ID: {member.id}")
                return await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        if member.bot:
            return
        data = await self.db.find_one({"_id": member.guild.id})
        if data is None:
            return
        else:
            if data['enabled'] is True:
                channel = self.bot.get_channel(data['channel'])
                embed = discord.Embed(
                    title="Member Left",
                    description=f"**Member:** {member.mention}",
                    color=discord.Color.red()
                )
                embed.set_thumbnail(url=member.avatar)
                embed.set_footer(
                    text=f"Member ID: {member.id}")
                return await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        if user.bot:
            return
        data = await self.db.find_one({"_id": guild.id})
        if data is None:
            return
        else:
            if data['enabled'] is True:
                channel = self.bot.get_channel(data['channel'])
                embed = discord.Embed(
                    title="Member Banned",
                    description=f"**Member:** {user}",
                    color=discord.Color.red()
                )
                embed.set_thumbnail(url=user.avatar)
                embed.set_footer(
                    text=f"Member ID: {user.id}")
                return await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        if user.bot:
            return
        data = await self.db.find_one({"_id": guild.id})
        if data is None:
            return
        else:
            if data['enabled'] is True:
                channel = self.bot.get_channel(data['channel'])
                embed = discord.Embed(
                    title="Member Unbanned",
                    description=f"**Member:** {user}",
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=user.avatar)
                embed.set_footer(
                    text=f"Member ID: {user.id}")
                return await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        if before.bot:
            return
        data = await self.db.find_one({"_id": before.guild.id})
        if data is None:
            return
        else:
            if data['enabled'] is True:
                channel = self.bot.get_channel(data['channel'])

                if before.nick != after.nick:
                    embed = discord.Embed(
                        title="Member Nickname Changed",
                        description=f"**Member:** {before.mention}\n"
                        f"**Before:** {before.nick}\n"
                        f"**After:** {after.nick}",
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=before.avatar.url)
                    embed.set_footer(
                        text=f"Member ID: {before.id}")
                    return await channel.send(embed=embed)

                elif before.roles != after.roles:
                    embed = discord.Embed(
                        title="Member Roles Changed",
                        description=f"**Member:** {before.mention}\n"
                        f"**Before:** {', '.join([role.mention for role in before.roles])}\n"
                        f"**After:** {', '.join([role.mention for role in after.roles])}",
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=before.avatar.url)
                    embed.set_footer(
                        text=f"Member ID: {before.id}")
                    return await channel.send(embed=embed)

                elif before.guild_avatar != after.guild_avatar:
                    embed = discord.Embed(
                        title="Member Guild Avatar Changed",
                        description=f"**Member:** {before.mention}\n"
                        f"**Before:** {before.guild_avatar}\n"
                        f"**After:** {after.guild_avatar}",
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=before.avatar.url)
                    embed.set_footer(
                        text=f"Member ID: {before.id}")
                    return await channel.send(embed=embed)

                elif before.pending != after.pending:
                    embed = discord.Embed(
                        title="Member Pending Changed",
                        description=f"**Member:** {before.mention}\n"
                        f"**Before:** {before.pending}\n"
                        f"**After:** {after.pending}",
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=before.avatar.url)
                    embed.set_footer(
                        text=f"Member ID: {before.id}")
                    return await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        data = await self.db.find_one({"_id": before.id})
        if data is None:
            return
        else:
            if data['enabled'] is True:
                channel = self.bot.get_channel(data['channel'])
                if before.name != after.name:
                    embed = discord.Embed(
                        title="Guild Name Changed",
                        description=f"**Before:** {before.name}\n"
                        f"**After:** {after.name}",
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=before.icon.url)
                    embed.set_footer(
                        text=f"Guild ID: {before.id}")
                    return await channel.send(embed=embed)
                elif before.icon != after.icon:
                    embed = discord.Embed(
                        title="Guild Icon Changed",
                        description=f"**Before:** {before.icon}\n"
                        f"**After:** {after.icon}",
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=before.icon.url)
                    embed.set_footer(
                        text=f"Guild ID: {before.id}")
                    return await channel.send(embed=embed)
                elif before.splash != after.splash:
                    embed = discord.Embed(
                        title="Guild Splash Changed",
                        description=f"**Before:** {before.splash}\n"
                        f"**After:** {after.splash}",
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=before.icon.url)
                    embed.set_footer(
                        text=f"Guild ID: {before.id}")
                    return await channel.send(embed=embed)
                elif before.discovery_splash != after.discovery_splash:
                    embed = discord.Embed(
                        title="Guild Discovery Splash Changed",
                        description=f"**Before:** {before.discovery_splash}\n"
                        f"**After:** {after.discovery_splash}",
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=before.icon.url)
                    embed.set_footer(
                        text=f"Guild ID: {before.id}")
                    return await channel.send(embed=embed)
                elif before.banner != after.banner:
                    embed = discord.Embed(
                        title="Guild Banner Changed",
                        description=f"**Before:** {before.banner}\n"
                        f"**After:** {after.banner}",
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=before.icon.url)
                    embed.set_footer(
                        text=f"Guild ID: {before.id}")
                    return await channel.send(embed=embed)
                elif before.owner != after.owner:
                    embed = discord.Embed(
                        title="Guild Owner Changed",
                        description=f"**Before:** {before.owner}\n"
                        f"**After:** {after.owner}",
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=before.icon.url)
                    embed.set_footer(
                        text=f"Guild ID: {before.id}")
                    return await channel.send(embed=embed)
                elif before.afk_channel != after.afk_channel:
                    embed = discord.Embed(
                        title="Guild AFK Channel Changed",
                        description=f"**Before:** {before.afk_channel}\n"
                        f"**After:** {after.afk_channel}",
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=before.icon)
                    embed.set_footer(
                        text=f"Guild ID: {before.id}")
                    return await channel.send(embed=embed)
                elif before.afk_timeout != after.afk_timeout:
                    embed = discord.Embed(
                        title="Guild AFK Timeout Changed",
                        description=f"**Before:** {before.afk_timeout}\n"
                        f"**After:** {after.afk_timeout}",
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=before.icon.url)
                    embed.set_footer(
                        text=f"Guild ID: {before.id}")
                    return await channel.send(embed=embed)
                elif before.widget_enabled != after.widget_enabled:
                    embed = discord.Embed(
                        title="Guild Widget Enabled Changed",
                        description=f"**Before:** {before.widget_enabled}\n"
                        f"**After:** {after.widget_enabled}",
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=before.icon.url)
                    embed.set_footer(
                        text=f"Guild ID: {before.id}")
                    return await channel.send(embed=embed)
                elif before.system_channel != after.system_channel:
                    embed = discord.Embed(
                        title="Guild System Channel Changed",
                        description=f"**Before:** {before.system_channel}\n"
                        f"**After:** {after.system_channel}",
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=before.icon.url)
                    embed.set_footer(
                        text=f"Guild ID: {before.id}")
                    return await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        data = await self.db.find_one({"_id": role.guild.id})
        if data is not None:
            channel = self.bot.get_channel(data["channel"])
            if data['enabled'] is True:
                embed = discord.Embed(
                    title="Guild Role Created",
                    description=f"**Name:** {role.name}\n**ID:** {role.id}",
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=role.guild.icon.url)
                embed.set_footer(
                    text=f"Guild ID: {role.guild.id}")
                return await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        data = await self.db.find_one({"_id": role.guild.id})
        if data is not None:
            channel = self.bot.get_channel(data["channel"])
            if data['enabled'] is True:
                embed = discord.Embed(
                    title="Guild Role Deleted",
                    description=f"**Name:** {role.name}\n**ID:** {role.id}",
                    color=discord.Color.red()
                )
                embed.set_thumbnail(url=role.guild.icon.url)
                embed.set_footer(
                    text=f"Guild ID: {role.guild.id}")
                return await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        data = await self.db.find_one({"_id": before.guild.id})
        if data is not None:
            channel = self.bot.get_channel(data["channel"])
            if data['enabled'] is True:
                if before.name != after.name:
                    embed = discord.Embed(
                        title="Guild Role Name Changed",
                        description=f"**Before:** {before.name}\n"
                        f"**After:** {after.name}",
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=before.guild.icon.url)
                    embed.set_footer(
                        text=f"Guild ID: {before.guild.id}")
                    return await channel.send(embed=embed)
                elif before.color != after.color:
                    embed = discord.Embed(
                        title="Guild Role Color Changed",
                        description=f"**Before:** {before.color}\n"
                        f"**After:** {after.color}",
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=before.guild.icon.url)
                    embed.set_footer(
                        text=f"Guild ID: {before.guild.id}")
                    return await channel.send(embed=embed)
                elif before.position != after.position:
                    embed = discord.Embed(
                        title="Guild Role position Changed",
                        description=f"**Role:** {before.mention}\n"
                        f"**Before:** {before.position}\n"
                        f"**After:** {after.position}",
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=before.guild.icon.url)
                    embed.set_footer(
                        text=f"Guild ID: {before.guild.id}")
                    return await channel.send(embed=embed)
                elif before.mentionable != after.mentionable:
                    embed = discord.Embed(
                        title="Guild Role Mentionable Changed",
                        description=f"**Before:** {before.mentionable}\n"
                        f"**After:** {after.mentionable}",
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=before.guild.icon.url)
                    embed.set_footer(
                        text=f"Guild ID: {before.guild.id}")
                    return await channel.send(embed=embed)
                elif before.permissions != after.permissions:
                    beforeperms = ", ".join([perm.replace("_", " ").title()
                                            for perm, value in before.permissions if value])
                    afterperms = ", ".join([perm.replace("_", " ").title()
                                            for perm, value in after.permissions if value])
                    embed = discord.Embed(
                        title="Guild Role Permissions Changed",
                        description=f"**Before:** {beforeperms}\n"
                        f"**After:** {afterperms}",
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=before.guild.icon.url)
                    embed.set_footer(
                        text=f"Guild ID: {before.guild.id}")
                    return await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_emojis_update(self, guild: discord.Guild, before: discord.Emoji, after: discord.Emoji):
        data = await self.db.find_one({"_id": guild.id})
        if data is not None:
            channel = self.bot.get_channel(data["channel"])
            if data['enabled'] is True:
                for emoji in before:
                    if emoji not in after:
                        embed = discord.Embed(
                            title="Guild Emoji Deleted",
                            description=f"**Name:** {emoji.name}\n**ID:** {emoji.id}",
                            color=discord.Color.red()
                        )
                        embed.set_image(url=emoji.url)
                        embed.set_thumbnail(url=guild.icon.url)
                        return await channel.send(embed=embed)
                for emoji in after:
                    if emoji not in before:
                        embed = discord.Embed(
                            title="Guild Emoji Created",
                            description=f"**Name:** {emoji.name}\n**ID:** {emoji.id}",
                            color=discord.Color.green()
                        )
                        embed.set_image(url=emoji.url)
                        embed.set_thumbnail(url=guild.icon.url)
                        return await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_guild_stickers_update(self, guild: discord.Guild, before: discord.Sticker, after: discord.Sticker):
        data = await self.db.find_one({"_id": guild.id})
        if data is not None:
            channel = self.bot.get_channel(data["channel"])
            if data['enabled'] is True:
                for sticker in before:
                    if sticker not in after:
                        embed = discord.Embed(
                            title="Guild Sticker Deleted",
                            description=f"**Name:** {sticker.name}\n**ID:** {sticker.id}",
                            color=discord.Color.red()
                        )
                        embed.set_image(url=sticker.url)
                        embed.set_thumbnail(url=guild.icon.url)
                        return await channel.send(embed=embed)
                for sticker in after:
                    if sticker not in before:
                        embed = discord.Embed(
                            title="Guild Sticker Created",
                            description=f"**Name:** {sticker.name}\n**ID:** {sticker.id}",
                            color=discord.Color.green()
                        )
                        embed.set_image(url=sticker.url)
                        embed.set_thumbnail(url=guild.icon.url)
                        return await channel.send(embed=embed)


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(ModLog(bot))
