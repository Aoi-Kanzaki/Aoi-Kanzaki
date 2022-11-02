import discord
from discord.ext import commands
from discord import app_commands as Fresh


class ModLog(commands.GroupCog, description="All ModLog related commands."):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.db = self.bot.db.automod

    @Fresh.command(name="enable")
    @Fresh.checks.has_permissions(administrator=True)
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
                content=f"Automod has been enabled! Logs will be sent to {channel.mention}"
            )
        else:
            if data['enabled'] is True:
                return await interaction.response.send_message(
                    "<:tickNo:697759586538749982> AutoMod is already enabled!")
            else:
                if data['channel'] is None:
                    channel = await interaction.guild.create_text_channel("modlog")
                    await self.db.update_one({"_id": interaction.guild.id}, {
                        "$set": {"enabled": True}})
                    await self.db.update_one({"_id": interaction.guild.id}, {
                        "$set": {"channel": channel.id}})
                    return await interaction.response.send_message(
                        content=f"Automod has been enabled! Logs will be sent to {channel.mention}"
                    )
                await self.db.update_one({"_id": interaction.guild.id}, {
                    "$set": {"enabled": True}})
                return await interaction.response.send_message(
                    "<:tickYes:697759553626046546> AutoMod has been enabled!")

    @Fresh.command(name="disable")
    @Fresh.checks.has_permissions(administrator=True)
    async def disable(self, interaction: discord.Interaction):
        """Disable modlog for this server."""
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            return await interaction.response.send_message(
                "<:tickNo:697759586538749982> AutoMod is not enabled!")
        else:
            if data['enabled'] is False:
                return await interaction.response.send_message(
                    "<:tickNo:697759586538749982> AutoMod is not enabled!")
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
                    "<:tickYes:697759553626046546> AutoMod has been disabled!")

    @commands.Cog.listener()
    async def on_message_edit(self, message: discord.Message, new_message: discord.Message):
        data = await self.db.find_one({"_id": message.guild.id})
        if message.author.bot:
            return
        if data is None:
            return
        else:
            if data['enabled'] is True:
                channel = self.bot.get_channel(data['channel'])
                embed = discord.Embed(
                    title="Message Edited",
                    description=f"**Author:** {message.author.mention}\n**Channel:** {message.channel.mention}\n**Before:** {message.content}\n**After:** {new_message.content}",
                    color=discord.Color.orange()
                )
                embed.set_thumbnail(url=message.author.avatar.url)
                embed.set_footer(
                    text=f"Message ID: {message.id} | Author ID: {message.author.id}")
                return await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        data = await self.db.find_one({"_id": message.guild.id})
        if message.author.bot:
            return
        if data is None:
            return
        else:
            if data['enabled'] is True:
                channel = self.bot.get_channel(data['channel'])
                embed = discord.Embed(
                    title="Message Deleted",
                    description=f"**Author:** {message.author.mention}\n**Channel:** {message.channel.mention}\n**Message:** {message.content}",
                    color=discord.Color.red()
                )
                embed.set_thumbnail(url=message.author.avatar.url)
                embed.set_footer(
                    text=f"Message ID: {message.id} | Author ID: {message.author.id}")
                return await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        data = await self.db.find_one({"_id": member.guild.id})
        if data is None:
            return
        else:
            if data['enabled'] is True:
                channel = self.bot.get_channel(data['channel'])
                embed = discord.Embed(
                    title="Member Joined",
                    description=f"**Member:** {member.mention}\n**Account Created:** {member.created_at.strftime('%d %B %Y')}",
                    color=discord.Color.green()
                )
                embed.set_thumbnail(url=member.avatar.url)
                embed.set_footer(
                    text=f"Member ID: {member.id}")
                return await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
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
        data = await self.db.find_one({"_id": before.guild.id})
        if data is None:
            return
        else:
            if data['enabled'] is True:
                channel = self.bot.get_channel(data['channel'])
                if before.nick != after.nick:
                    embed = discord.Embed(
                        title="Member Nickname Changed",
                        description=f"**Member:** {before.mention}\n**Before:** {before.nick}\n**After:** {after.nick}",
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=before.avatar.url)
                    embed.set_footer(
                        text=f"Member ID: {before.id}")
                    return await channel.send(embed=embed)
                elif before.roles != after.roles:
                    embed = discord.Embed(
                        title="Member Roles Changed",
                        description=f"**Member:** {before.mention}\n**Before:** {', '.join([role.mention for role in before.roles])}\n**After:** {', '.join([role.mention for role in after.roles])}",
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=before.avatar.url)
                    embed.set_footer(
                        text=f"Member ID: {before.id}")
                    return await channel.send(embed=embed)
                elif before.guild_avatar != after.guild_avatar:
                    embed = discord.Embed(
                        title="Member Guild Avatar Changed",
                        description=f"**Member:** {before.mention}\n**Before:** {before.guild_avatar}\n**After:** {after.guild_avatar}",
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=before.avatar.url)
                    embed.set_footer(
                        text=f"Member ID: {before.id}")
                    return await channel.send(embed=embed)
                elif before.pending != after.pending:
                    embed = discord.Embed(
                        title="Member Pending Changed",
                        description=f"**Member:** {before.mention}\n**Before:** {before.pending}\n**After:** {after.pending}",
                        color=discord.Color.orange()
                    )
                    embed.set_thumbnail(url=before.avatar.url)
                    embed.set_footer(
                        text=f"Member ID: {before.id}")
                    return await channel.send(embed=embed)


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(ModLog(bot))
