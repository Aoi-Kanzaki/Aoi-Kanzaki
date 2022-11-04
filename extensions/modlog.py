import discord
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

    @commands.Cog.listener()
    async def on_message_edit(self, message: discord.Message, new_message: discord.Message):
        if message.author.bot:
            return
        data = await self.db.find_one({"_id": message.guild.id})
        if data is None:
            return
        else:
            if data['enabled'] is True:
                channel = self.bot.get_channel(data['channel'])
                embed = discord.Embed(
                    title="Message Edited",
                    description=f"**Author:** {message.author.mention}\n"
                    f"**Channel:** {message.channel.mention}\n"
                    f"**Before:** {message.content}\n"
                    f"**After:** {new_message.content}",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=message.author.avatar.url)
                embed.set_footer(
                    text=f"Message ID: {message.id} | Author ID: {message.author.id}")
                return await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if message.author.bot:
            return
        data = await self.db.find_one({"_id": message.guild.id})
        if data is None:
            return
        else:
            if data['enabled'] is True:
                channel = self.bot.get_channel(data['channel'])
                embed = discord.Embed(
                    title="Message Deleted",
                    description=f"**Author:** {message.author.mention}\n"
                    f"**Channel:** {message.channel.mention}\n"
                    f"**Message:** {message.content}",
                    color=discord.Color.red()
                )
                embed.set_thumbnail(url=message.author.avatar.url)
                embed.set_footer(
                    text=f"Message ID: {message.id} | Author ID: {message.author.id}")
                return await channel.send(embed=embed)

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
                    f"**Account Created:** {member.created_at.strftime('%d %B %Y')}",
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=member.avatar.url)
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
                embed.set_thumbnail(url=member.avatar.url)
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
                    description=f"**Member:** {user.mention}",
                    color=discord.Color.red()
                )
                embed.set_thumbnail(url=user.avatar.url)
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
                    description=f"**Member:** {user.mention}",
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=user.avatar.url)
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
                elif before.region != after.region:
                    embed = discord.Embed(
                        title="Guild Region Changed",
                        description=f"**Before:** {before.region}\n"
                        f"**After:** {after.region}",
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
                    embed.set_thumbnail(url=before.icon.url)
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
                elif before.widget_channel != after.widget_channel:
                    embed = discord.Embed(
                        title="Guild Widget Channel Changed",
                        description=f"**Before:** {before.widget_channel}\n"
                        f"**After:** {after.widget_channel}",
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
            elif before.hoist != after.hoist:
                embed = discord.Embed(
                    title="Guild Role Hoist Changed",
                    description=f"**Before:** {before.hoist}\n"
                    f"**After:** {after.hoist}",
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
                embed = discord.Embed(
                    title="Guild Role Permissions Changed",
                    description=f"**Before:** {before.permissions}\n"
                    f"**After:** {after.permissions}",
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
            if before != after:
                embed = discord.Embed(
                    title="Guild Emoji Updated",
                    description=f"**Before:** {before}\n"
                    f"**After:** {after}",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=guild.icon.url)
                embed.set_footer(
                    text=f"Guild ID: {guild.id}")
                return await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_channel_create(self, channel: discord.abc.GuildChannel):
        data = await self.db.find_one({"_id": channel.guild.id})
        if data is not None:
            channel = self.bot.get_channel(data["channel"])
            embed = discord.Embed(
                title="Channel Created",
                description=f"**Name:** {channel.name}\n"
                f"**ID:** {channel.id}",
                color=discord.Color.green()
            )
            embed.set_thumbnail(url=channel.guild.icon.url)
            embed.set_footer(
                text=f"Guild ID: {channel.guild.id}")
            return await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_channel_delete(self, channel: discord.abc.GuildChannel):
        data = await self.db.find_one({"_id": channel.guild.id})
        if data is not None:
            channel = self.bot.get_channel(data["channel"])
            embed = discord.Embed(
                title="Channel Deleted",
                description=f"**Name:** {channel.name}\n"
                f"**ID:** {channel.id}",
                color=discord.Color.red()
            )
            embed.set_thumbnail(url=channel.guild.icon.url)
            embed.set_footer(
                text=f"Guild ID: {channel.guild.id}")
            return await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        data = await self.db.find_one({"_id": before.guild.id})
        if data is not None:
            channel = self.bot.get_channel(data["channel"])
            if before.name != after.name:
                embed = discord.Embed(
                    title="Channel Name Changed",
                    description=f"**Before:** {before.name}\n"
                    f"**After:** {after.name}",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=before.guild.icon.url)
                embed.set_footer(
                    text=f"Guild ID: {before.guild.id}")
                return await channel.send(embed=embed)
            elif before.category != after.category:
                embed = discord.Embed(
                    title="Channel Category Changed",
                    description=f"**Before:** {before.category}\n"
                    f"**After:** {after.category}",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=before.guild.icon.url)
                embed.set_footer(
                    text=f"Guild ID: {before.guild.id}")
                return await channel.send(embed=embed)
            elif before.position != after.position:
                embed = discord.Embed(
                    title="Channel Position Changed",
                    description=f"**Before:** {before.position}\n"
                    f"**After:** {after.position}",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=before.guild.icon.url)
                embed.set_footer(
                    text=f"Guild ID: {before.guild.id}")
                return await channel.send(embed=embed)
            elif before.topic != after.topic:
                embed = discord.Embed(
                    title="Channel Topic Changed",
                    description=f"**Before:** {before.topic}\n"
                    f"**After:** {after.topic}",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=before.guild.icon.url)
                embed.set_footer(
                    text=f"Guild ID: {before.guild.id}")
                return await channel.send(embed=embed)
            elif before.slowmode_delay != after.slowmode_delay:
                embed = discord.Embed(
                    title="Channel Slowmode Delay Changed",
                    description=f"**Before:** {before.slowmode_delay}\n"
                    f"**After:** {after.slowmode_delay}",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=before.guild.icon.url)
                embed.set_footer(
                    text=f"Guild ID: {before.guild.id}")
                return await channel.send(embed=embed)
            elif before.is_nsfw() != after.is_nsfw():
                embed = discord.Embed(
                    title="Channel NSFW Changed",
                    description=f"**Before:** {before.is_nsfw()}\n"
                    f"**After:** {after.is_nsfw()}",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=before.guild.icon.url)
                embed.set_footer(
                    text=f"Guild ID: {before.guild.id}")
                return await channel.send(embed=embed)
            elif before.is_news() != after.is_news():
                embed = discord.Embed(
                    title="Channel News Changed",
                    description=f"**Before:** {before.is_news()}\n"
                    f"**After:** {after.is_news()}",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=before.guild.icon.url)
                embed.set_footer(
                    text=f"Guild ID: {before.guild.id}")
                return await channel.send(embed=embed)
            elif before.is_private() != after.is_private():
                embed = discord.Embed(
                    title="Channel Private Changed",
                    description=f"**Before:** {before.is_private()}\n"
                    f"**After:** {after.is_private()}",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=before.guild.icon.url)
                embed.set_footer(
                    text=f"Guild ID: {before.guild.id}")
                return await channel.send(embed=embed)
            elif before.is_voice() != after.is_voice():
                embed = discord.Embed(
                    title="Channel Voice Changed",
                    description=f"**Before:** {before.is_voice()}\n"
                    f"**After:** {after.is_voice()}",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=before.guild.icon.url)
                embed.set_footer(
                    text=f"Guild ID: {before.guild.id}")
                return await channel.send(embed=embed)
            elif before.is_text() != after.is_text():
                embed = discord.Embed(
                    title="Channel Text Changed",
                    description=f"**Before:** {before.is_text()}\n"
                    f"**After:** {after.is_text()}",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=before.guild.icon.url)
                embed.set_footer(
                    text=f"Guild ID: {before.guild.id}")
                return await channel.send(embed=embed)
            elif before.is_category() != after.is_category():
                embed = discord.Embed(
                    title="Channel Category Changed",
                    description=f"**Before:** {before.is_category()}\n"
                    f"**After:** {after.is_category()}",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=before.guild.icon.url)
                embed.set_footer(
                    text=f"Guild ID: {before.guild.id}")
                return await channel.send(embed=embed)
            elif before.is_store() != after.is_store():
                embed = discord.Embed(
                    title="Channel Store Changed",
                    description=f"**Before:** {before.is_store()}\n"
                    f"**After:** {after.is_store()}",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=before.guild.icon.url)
                embed.set_footer(
                    text=f"Guild ID: {before.guild.id}")
                return await channel.send(embed=embed)
            elif before.is_stage_voice() != after.is_stage_voice():
                embed = discord.Embed(
                    title="Channel Stage Voice Changed",
                    description=f"**Before:** {before.is_stage_voice()}\n"
                    f"**After:** {after.is_stage_voice()}",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=before.guild.icon.url)
                embed.set_footer(
                    text=f"Guild ID: {before.guild.id}")
                return await channel.send(embed=embed)
            elif before.default_auto_archive_duration != after.default_auto_archive_duration:
                embed = discord.Embed(
                    title="Channel Default Auto Archive Duration Changed",
                    description=f"**Before:** {before.default_auto_archive_duration}\n"
                    f"**After:** {after.default_auto_archive_duration}",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=before.guild.icon.url)
                embed.set_footer(
                    text=f"Guild ID: {before.guild.id}")
                return await channel.send(embed=embed)
            elif before.rtc_region != after.rtc_region:
                embed = discord.Embed(
                    title="Channel RTC Region Changed",
                    description=f"**Before:** {before.rtc_region}\n"
                    f"**After:** {after.rtc_region}",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=before.guild.icon.url)
                embed.set_footer(
                    text=f"Guild ID: {before.guild.id}")
                return await channel.send(embed=embed)
            elif before.bitrate != after.bitrate:
                embed = discord.Embed(
                    title="Channel Bitrate Changed",
                    description=f"**Before:** {before.bitrate}\n"
                    f"**After:** {after.bitrate}",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=before.guild.icon.url)
                embed.set_footer(
                    text=f"Guild ID: {before.guild.id}")
                return await channel.send(embed=embed)
            elif before.user_limit != after.user_limit:
                embed = discord.Embed(
                    title="Channel User Limit Changed",
                    description=f"**Before:** {before.user_limit}\n"
                    f"**After:** {after.user_limit}",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=before.guild.icon.url)
                embed.set_footer(
                    text=f"Guild ID: {before.guild.id}")
                return await channel.send(embed=embed)
            elif before.slowmode_delay != after.slowmode_delay:
                embed = discord.Embed(
                    title="Channel Slowmode Delay Changed",
                    description=f"**Before:** {before.slowmode_delay}\n"
                    f"**After:** {after.slowmode_delay}",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=before.guild.icon.url)
                embed.set_footer(
                    text=f"Guild ID: {before.guild.id}")
                return await channel.send(embed=embed)


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(ModLog(bot))
