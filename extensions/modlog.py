import discord
import datetime
from discord.ext import commands
from typing import Literal, Optional
from discord import app_commands as Aoi


class ModLog(commands.GroupCog, description="All ModLog related commands."):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.db = self.bot.db.modlog

    @Aoi.command(name="settings")
    async def setting(self, interaction: discord.Interaction,
                      setting: Literal['Messages', 'Channels', 'Guild Join-Leave', 'Voice Join-Leave', 'Roles', 'Guild', 'Members', 'Bans']):
        """Toggle on or off certain logs."""
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            data = {
                "_id": interaction.guild.id,
                "enabled": False,
                "channel": None,
                "events": [setting]
            }
            await self.db.insert_one(data)
            return await interaction.response.send_message(
                f"I have enabled {setting} events! Please make sure to run `/mod-log toggle` to setup the channel."
            )
        if setting in data['events']:
            await self.db.update_one({"_id": interaction.guild.id}, {"$pull": {"events": setting}})
            return await interaction.response.send_message(
                f"I have disabled {setting} events!"
            )
        await self.db.update_one({"_id": interaction.guild.id}, {"$push": {"events": setting}})
        return await interaction.response.send_message(
            f"I have enabled {setting} events!"
        )

    @Aoi.command(name="toggle")
    async def toggle(self, interaction: discord.Interaction, toggle: Literal['enable', 'disable']):
        """Enable or disable the modlog system."""
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            if toggle == 'enable':
                data = {
                    "_id": interaction.guild.id,
                    "enabled": True,
                    "channel": None,
                    "events": []
                }
                await self.db.insert_one(data)
                return await interaction.response.send_message("Mod-Log has been enabled.")
            return await interaction.response.send_message("Mod-Log is already disabled.")
        t = False
        if toggle == 'enable':
            t = True
        data['enabled'] = t
        await self.db.update_one({"_id": interaction.guild.id}, {"$set": data})
        return await interaction.response.send_message(f"I have {toggle}d the Mod-Log system.")

    @Aoi.command(name="channel")
    async def channel(self, interaction: discord.Interaction, channel: Optional[discord.TextChannel]):
        """Set the modlog channel."""
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            if channel != None:
                channelID = channel.id
            else:
                c = await interaction.guild.create_text_channel(name="mod-log", reason=f"{interaction.user} enabled modlog system.")
                channelID = c.id
            data = {
                "_id": interaction.guild.id,
                "enabled": False,
                "channel": channelID,
                "events": []
            }
            await self.db.insert_one(data)
            return await interaction.response.send_message(
                f"I have enabled the modlog system and set the channel, enabled events using `/mod-log settings`!"
            )
        if channel != None:
            if channel.id == data['channel']:
                return await interaction.response.send_message("That is already the modlog channel!")
            channelID = channel.id
        else:
            for ch in interaction.guild.channels:
                if ch.id == data['channel']:
                    return await interaction.response.send_message(f"The modlog channel is already set to {ch.mention}")
            c = await interaction.guild.create_text_channel(name="mod-log", reason=f"{interaction.user} enabled modlog system.")
            channelID = c.id
        data['channel'] = channelID
        await self.db.update_one({"_id": interaction.guild.id}, {"$set": data})
        return await interaction.response.send_message(
            f"I have set the modlog channel to <#{channelID}>!"
        )

    @Aoi.command(name="config")
    async def config(self, interaction: discord.Interaction):
        """Shows the config settings for the current guild."""
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            return await interaction.response.send_message("Mod-Log has not been setup for this guild!")
        e = discord.Embed(colour=discord.Colour.teal())
        e.set_author(name="Mod-Log Config", icon_url=interaction.guild.icon)
        e.add_field(name="Toggle:", value=(
            "Enabled." if data['enabled'] is True else "Disabled."))
        e.add_field(name="Log Channel:", value=(
            f"<#{data['channel']}>" if data['channel'] is not None else "Not set."))
        events = "\n".join(e for e in data['events'])
        e.add_field(name="Enabled Events:", value=(
            f"{events}" if data['events'] != [] else "No events enabled."), inline=False)
        return await interaction.response.send_message(embed=e)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if not message.guild or message.author.bot:
            return
        data = await self.db.find_one({"_id": message.guild.id})
        if data != None and data['enabled'] is True and "Messages" in data['events']:
            e = discord.Embed(colour=discord.Colour.red(),
                              timestamp=datetime.datetime.now())
            e.set_author(name=message.author,
                         icon_url=message.author.display_avatar)
            e.description = f"Messaged deleted in {message.channel.mention}"
            e.add_field(name="Content:", value=message.content, inline=False)

            channel = await message.guild.fetch_channel(data['channel'])
            if channel != None:
                return await channel.send(embed=e)

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        if not before.guild or before.author.bot:
            return
        data = await self.db.find_one({"_id": before.guild.id})
        if data != None and data['enabled'] is True and 'Messages' in data['events'] and before.content != after.content:
            e = discord.Embed(colour=discord.Colour.orange(),
                              timestamp=datetime.datetime.now())
            e.set_author(name=before.author,
                         icon_url=before.author.display_avatar)
            e.description = f"Message Edited in {before.channel.mention}"
            e.add_field(name="Before:", value=before.content, inline=False)
            e.add_field(name="After:", value=after.content)

            channel = await before.guild.fetch_channel(data['channel'])
            if channel != None:
                return await channel.send(embed=e)

    @commands.Cog.listener()
    async def on_voice_state_update(self, member: discord.Member, before: discord.VoiceState, after: discord.VoiceState):
        if not member.guild or member.bot:
            return
        data = await self.db.find_one({"_id": member.guild.id})
        if data != None and data['enabled'] is True and 'Voice Join-Leave' in data['events']:
            e = discord.Embed(colour=discord.Colour.fuchsia(),
                              timestamp=datetime.datetime.now(),
                              description="Member voice status has changed")
            e.set_author(name=member.name, icon_url=member.display_avatar)

            if before.channel != after.channel:
                if before.channel != None:
                    e.add_field(
                        name="Left:", value=f"{before.channel.mention} ({before.channel.name})", inline=False)
                if member.voice is not None:
                    e.add_field(
                        name="Joined:", value=f"{after.channel.mention} ({after.channel.name})", inline=False)
            if before.self_deaf != after.self_deaf:
                e.add_field(
                    name="Self Deafened:", value=f"**Before:** {before.self_deaf}\n**After:** {after.self_deaf}")
            if before.self_mute != after.self_mute:
                e.add_field(
                    name="Self Muted:", value=f"**Before:** {before.self_mute}\n**After:** {after.self_mute}")
            if before.self_stream != after.self_stream:
                e.add_field(
                    name="Streaming:", value=f"**Before:** {before.self_stream}\n**After:** {after.self_stream}")
            if before.self_video != after.self_video:
                e.add_field(
                    name="Camera:", value=f"**Before:** {before.self_video}\n**After:** {after.self_video}")
            if before.mute != after.mute:
                e.add_field(
                    name="Server Muted:", value=f"**Before:** {before.mute}\n**After:** {after.mute}")
            if before.deaf != after.deaf:
                e.add_field(
                    name="Server Deafened:", value=f"**Before:** {before.deaf}\n**After:** {after.deaf}")

            channel = await member.guild.fetch_channel(data['channel'])
            if channel != None:
                return await channel.send(embed=e)

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        data = await self.db.find_one({"_id": member.guild.id})
        if data != None and data['enabled'] is True and 'Guild Join-Leave' in data['events']:
            e = discord.Embed(colour=discord.Colour.green(),
                              timestamp=datetime.datetime.now(),
                              description="Member has joined")
            e.set_author(name=member.name, icon_url=member.display_avatar)
            e.add_field(name="ID:", value=member.id, inline=False)
            e.add_field(name="Account Created:",
                        value=member.created_at.date())

            channel = await member.guild.fetch_channel(data['channel'])
            if channel != None:
                return await channel.send(embed=e)

    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member):
        data = await self.db.find_one({"_id": member.guild.id})
        if data != None and data['enabled'] is True and 'Guild Join-Leave' in data['events']:
            e = discord.Embed(colour=discord.Colour.red(),
                              timestamp=datetime.datetime.now(),
                              description="Member has left")
            e.set_author(name=member.name, icon_url=member.display_avatar)
            e.add_field(name="ID:", value=member.id, inline=False)
            e.add_field(name="Joined:", value=member.joined_at.date())
            e.add_field(name="Account Created:",
                        value=member.created_at.date())

            channel = await member.guild.fetch_channel(data['channel'])
            if channel != None:
                return await channel.send(embed=e)

    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User):
        data = await self.db.find_one({"_id": guild.id})
        if data != None and data['enabled'] is True and 'Bans' in data['events']:
            e = discord.Embed(colour=discord.Colour.yellow(),
                              timestamp=datetime.datetime.now(),
                              description="Member has been unbanned")
            e.set_author(name=user.name, icon_url=user.display_avatar)

            channel = await guild.fetch_channel(data['channel'])
            if channel != None:
                return await channel.send(embed=e)

    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User):
        data = await self.db.find_one({"_id": guild.id})
        if data != None and data['enabled'] is True and 'Bans' in data['events']:
            e = discord.Embed(colour=discord.Colour.red(),
                              timestamp=datetime.datetime.now(),
                              description="Member has been banned")
            e.set_author(name=user.name, icon_url=user.display_avatar)

            channel = await guild.fetch_channel(data['channel'])
            if channel != None:
                return await channel.send(embed=e)

    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member):
        data = await self.db.find_one({"_id": before.guild.id})
        if data != None and data['enabled'] is True and 'Members' in data['events']:
            channel = await before.guild.fetch_channel(data['channel'])
            if channel is None:
                return
            e = discord.Embed(colour=discord.Colour.magenta(),
                              timestamp=datetime.datetime.now())
            e.set_author(name=before.name, icon_url=before.display_avatar)
            e.add_field(
                name="Member:", value=f"{before.mention} ({before.name}, {before.id})", inline=False)
            if before.nick != after.nick:
                e.description = "Member nickname has been updated"
                if before.nick != None:
                    e.add_field(name="Before:", value=before.nick)
                if after.nick == None:
                    e.description = "Member has removed their nickname"
                else:
                    e.add_field(name="After:", value=after.nick)
                return await channel.send(embed=e)
            if before.name != after.name:
                e.description = "Member has changed their name"
                e.add_field(name="Before:", after=before.name)
                e.add_field(name="After:", value=after.name)
                return await channel.send(embed=e)
            if before.roles != after.roles:
                e.description = "Member roles updated\n\n"
                addedroles = [e for e in after.roles if e not in before.roles]
                removedroles = [
                    e for e in before.roles if e not in after.roles]
                if addedroles != []:
                    e.description += "➕ {}\n".format(
                        ", ".join(e.name for e in addedroles))
                if removedroles != []:
                    e.description += "➖ {}\n".format(
                        ", ".join(e.name for e in removedroles))
                return await channel.send(embed=e)
            if before.display_avatar != after.display_avatar:
                e.description = "Member avatar updated"
                e.add_field(name="Before:",
                            value=before.display_avatar.url, inline=False)
                e.add_field(name="After:",
                            value=after.display_avatar.url, inline=False)
                return await channel.send(embed=e)

    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role):
        data = await self.db.find_one({"_id": role.guild.id})
        if data != None and data['enabled'] is True and 'Roles' in data['events']:
            e = discord.Embed(colour=discord.Colour.green(),
                              timestamp=datetime.datetime.now(),
                              description="Guild role has been created")
            e.set_author(name=role.guild.name, icon_url=role.guild.icon)
            e.add_field(name="Name:", value=role.name)
            e.add_field(name="ID:", value=role.id)

            channel = await role.guild.fetch_channel(data['channel'])
            if channel != None:
                return await channel.send(embed=e)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        data = await self.db.find_one({"_id": role.guild.id})
        if data != None and data['enabled'] is True and 'Roles' in data['events']:
            e = discord.Embed(colour=discord.Colour.red(),
                              timestamp=datetime.datetime.now(),
                              description="Guild role has been deleted")
            e.set_author(name=role.guild.name, icon_url=role.guild.icon)
            e.add_field(name="Name:", value=role.name)
            e.add_field(name="ID:", value=role.id)

            channel = await role.guild.fetch_channel(data['channel'])
            if channel != None:
                return await channel.send(embed=e)

    @commands.Cog.listener()
    async def on_guild_role_update(self, before: discord.Role, after: discord.Role):
        data = await self.db.find_one({"_id": before.guild.id})
        if data != None and data['enabled'] is True and 'Roles' in data['events']:
            channel = await before.guild.fetch_channel(data['channel'])
            if channel is None:
                return
            e = discord.Embed(colour=discord.Colour.orange(),
                              timestamp=datetime.datetime.now(),
                              description="Guild role has been updated")
            e.set_author(name=before.guild.name, icon_url=after.guild.icon)
            e.add_field(
                name="Role:", value=f"{before.mention} ({before.name}, {before.id})", inline=False)
            if before.name != after.name:
                e.add_field(
                    name="Name:", value=f"**Before:** {before.name}\n**After:** {after.name}")
            if before.color != after.color:
                e.add_field(
                    name="Color:", value=f"**Before:** {before.colour}\n**After:** {after.color}")
            if before.icon != after.icon:
                e.add_field(
                    name="Icon:", value=(f"**Before:** {before.icon}\n**After:** {after.icon}" if before.icon != None else f"**After:** {after.position}"))
            if before.hoist != after.hoist:
                e.add_field(
                    name="Hoist:", value=f"**Before:** {before.hoist}\n**After:** {after.hoist}")
            if before.mentionable != after.mentionable:
                e.add_field(
                    name="Mentionable:", value=f"**Before:** {before.mentionable}\n**After:** {after.mentionable}")
            if before.unicode_emoji != after.unicode_emoji:
                e.add_field(
                    name="Emoji:", value=f"**Before:** {before.unicode_emoji}\n**After:** {after.unicode_emoji}")
            if before.permissions != after.permissions:
                changed = [
                    e for e in after.permissions if e not in before.permissions]
                granted = []
                denied = []
                for name, value in changed:
                    if value is True:
                        granted.append(name)
                    else:
                        denied.append(name)
                if granted != [] and denied != []:
                    e.add_field(name="Permissions:", value="➕ {}\n➖ {}".format(
                        ", ".join(e for e in granted),
                        ", ".join(e for e in denied)),
                        inline=False)
                if granted != [] and denied == []:
                    e.add_field(name="Permissions:", value="➕ {}".format(
                        ", ".join(e for e in granted)),
                        inline=False)
                if denied != [] and granted == []:
                    e.add_field(name="Permissions:", value="➖ {}".format(
                        ", ".join(e for e in denied)),
                        inline=False)
            return await channel.send(embed=e)

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel):
        data = await self.db.find_one({"_id": channel.guild.id})
        if data != None and data['enabled'] is True and 'Channels' in data['events']:
            e = discord.Embed(colour=discord.Colour.green(),
                              timestamp=datetime.datetime.now(),
                              description="Guild channel has been created")
            e.set_author(name=channel.guild.name, icon_url=channel.guild.icon)
            e.add_field(
                name="Name:", value=f"{channel.mention} ({channel.id})", inline=False)
            e.add_field(name="Channel Type:", value=channel.type)
            if channel.category != None:
                e.add_field(name="Category:", value=channel.category)

            ch = await channel.guild.fetch_channel(data['channel'])
            if ch != None:
                return await ch.send(embed=e)

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel):
        data = await self.db.find_one({"_id": channel.guild.id})
        if data != None and data['enabled'] is True and 'Channels' in data['events']:
            e = discord.Embed(colour=discord.Colour.red(),
                              timestamp=datetime.datetime.now(),
                              description="Guild channel has been deleted")
            e.set_author(name=channel.guild.name, icon_url=channel.guild.icon)
            e.add_field(
                name="Name:", value=f"{channel.mention} ({channel.id})", inline=False)
            e.add_field(name="Channel Type:", value=channel.type)
            if channel.category != None:
                e.add_field(name="Category:", value=channel.category)

            ch = await channel.guild.fetch_channel(data['channel'])
            if ch != None:
                return await ch.send(embed=e)

    @commands.Cog.listener()
    async def on_guild_channel_update(self, before: discord.abc.GuildChannel, after: discord.abc.GuildChannel):
        data = await self.db.find_one({"_id": before.guild.id})
        if data != None and data['enabled'] is True and 'Channels' in data['events']:
            e = discord.Embed(colour=discord.Colour.orange(),
                              timestamp=datetime.datetime.now(),
                              description="Guild channel has been updated")
            e.set_author(name=before.guild.name, icon_url=after.guild.icon)
            e.add_field(
                name="Channel:", value=f"{before.mention} ({before.name}, {before.id})", inline=False)
            if before.name != after.name:
                e.add_field(
                    name="Name:", value=f"**Before:** {before.name}\n**After:** {after.name}")
            if before.category != after.category:
                e.add_field(
                    name="Category:", value=f"**Before:** {before.category}\n**After:** {after.category}")
            if before.position != after.position:
                e.add_field(
                    name="Position:", value=f"**Before:** {before.position}\n**After:** {after.position}")
            if before.overwrites != after.overwrites:
                granted = []
                denied = []
                for override in before.overwrites:
                    if override in before.overwrites and override in after.overwrites:
                        pass
                    elif override in after.overwrites and override not in before.overwrites:
                        granted.append(override)
                    elif override in before.overwrites and override not in after.overwrites:
                        denied.append(override)
                for override in after.overwrites:
                    if override in before.overwrites and override in after.overwrites:
                        pass
                    elif override in after.overwrites and override not in before.overwrites:
                        granted.append(override)
                    elif override in before.overwrites and override not in after.overwrites:
                        denied.append(override)

                if granted == [] and denied == []:
                    return
                else:
                    if granted != [] and denied != []:
                        e.add_field(name="Overwrites:", value="➕ {}\n➖ {}".format(
                            ", ".join(e.name for e in granted),
                            ", ".join(e.name for e in denied)))
                    elif granted != [] and denied == []:
                        e.add_field(name="Overwrites:", value="➕ {}".format(
                            ", ".join(e.name for e in granted)))
                    elif granted == [] and denied != []:
                        e.add_field(name="Overwrites:", value="➖ {}".format(
                            ", ".join(e.name for e in denied)))

            channel = await before.guild.fetch_channel(data['channel'])
            if channel != None:
                return await channel.send(embed=e)

    @commands.Cog.listener()
    async def on_guild_update(self, before: discord.Guild, after: discord.Guild):
        data = await self.db.find_one({"_id": before.id})
        if data != None and data['enabled'] is True and 'Guild' in data['events']:
            e = discord.Embed(colour=discord.Colour.orange(),
                              timestamp=datetime.datetime.now(),
                              description="Guild has been updated")
            e.set_author(name=before.name, icon_url=before.icon)
            if before.name != after.name:
                e.add_field(
                    name="Name:", value=f"**Before:** {before.name}\n**After:** {after.name}")
            if before.afk_channel != after.afk_channel:
                beforec = (
                    before.afk_channel.name if before.afk_channel is not None else None)
                afterc = (
                    after.afk_channel.name if after.afk_channel is not None else None)
                e.add_field(
                    name="Afk Channel:", value=f"**Before:** {beforec}\n**After:** {afterc}")
            if before.afk_timeout != after.afk_timeout:
                e.add_field(
                    name="Afk Timeout:", value=f"**Before:** {round(before.afk_timeout / 60)} minutes.\n**After:** {round(after.afk_timeout / 60)} minutes.")
            if before.default_notifications != after.default_notifications:
                e.add_field(
                    name="Notifications:", value=f"**Before:** {str(before.default_notifications).split('.')[1]}\n**After:** {str(after.default_notifications).split('.')[1]}")
            if before.verification_level != after.verification_level:
                e.add_field(
                    name="Verification:", value=f"**Before:** {before.verification_level}\n**After:** {after.verification_level}")
            if before.banner != after.banner:
                e.add_field(
                    name="Banner:", value=f"**Before:** {before.banner.url}\n**After:** {after.banner.url}")
            if before.icon != after.icon:
                e.add_field(
                    name="Banner:", value=f"**Before:** {before.icon.url}\n**After:** {after.icon.url}")
            if before.categories != after.categories:
                beforec = [
                    e for e in after.categories if e not in before.categories]
                afterc = [
                    e for e in before.categories if e not in after.categories]
                added = []
                removed = []
                for c in afterc:
                    if c not in beforec:
                        removed.append(c.name)
                    else:
                        added.append(c.name)
                if added == [] and removed == []:
                    return
                else:
                    if added != [] and removed != []:
                        e.add_field(name="Categories:", value="➕ {}\n➖ {}".format(
                            ", ".join(e.name for e in added),
                            ", ".join(e.name for e in removed)))
                    elif added != [] and removed == []:
                        e.add_field(name="Categories:", value="➕ {}".format(
                            ", ".join(e.name for e in added)))
                    elif added == [] and removed != []:
                        e.add_field(name="Categories:", value="➖ {}".format(
                            ", ".join(e.name for e in removed)))

            channel = await before.fetch_channel(data['channel'])
            if channel != None:
                return await channel.send(embed=e)


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(ModLog(bot))
