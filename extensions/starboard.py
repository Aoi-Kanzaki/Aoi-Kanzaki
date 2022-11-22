import discord
import typing
import random
from discord.ext import commands
from discord import app_commands as Aoi


class Starboard(commands.GroupCog, description="Starboard commands."):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.db = self.bot.db.starboard

    @Aoi.command(name="toggle", description="Toggle starboard on/off.")
    @Aoi.describe(toggle="Whether to turn starboard on or off.")
    @Aoi.checks.has_permissions(manage_guild=True)
    async def toggle(self, interaction: discord.Interaction, toggle: typing.Literal["enable", "disable"]):
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            if toggle == "enable":
                channel = await interaction.guild.create_text_channel(name="starboard", reason="Starboard setup.")
                data = {
                    "_id": interaction.guild.id,
                    "enabled": True,
                    "channel": channel.id,
                    "messages": [],
                    "ignored": [],
                    "count": 3
                }
                await self.db.insert_one(data)
                return await interaction.response.send_message("Starboard has been enabled.", ephemeral=True)
            return await interaction.response.send_message("Starboard is already disabled.", ephemeral=True)
        else:
            if toggle == "enable":
                if data["enabled"]:
                    return await interaction.response.send_message("Starboard is already enabled.", ephemeral=True)
                else:
                    channel = await interaction.guild.create_text_channel(name="starboard", reason="Starboard setup.")
                    await self.db.update_one({"_id": interaction.guild.id}, {"$set": {"enabled": True, "channel": channel.id}})
                    return await interaction.response.send_message("Starboard has been enabled.", ephemeral=True)
            else:
                if not data["enabled"]:
                    return await interaction.response.send_message("Starboard is already disabled.", ephemeral=True)
                else:
                    channel = interaction.guild.get_channel(data["channel"])
                    await channel.delete(reason="Starboard disabled.")
                    await self.db.update_one({"_id": interaction.guild.id}, {"$set": {"enabled": False, "channel": None, "messages": [], "count": 3, "ignored": []}})
                    return await interaction.response.send_message("Starboard has been disabled.", ephemeral=True)

    @Aoi.command(name="ignore-channel", description="Ignore a channel from the starboard.")
    @Aoi.describe(channel="The channel to ignore.")
    @Aoi.checks.has_permissions(manage_guild=True)
    async def ignore_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            return await interaction.response.send_message("Starboard is not enabled.", ephemeral=True)
        else:
            if channel.id in data["ignored"]:
                await self.db.update_one({"_id": interaction.guild.id}, {"$pull": {"ignored": channel.id}})
                return await interaction.response.send_message(f"{channel.mention} is no longer ignored.", ephemeral=True)
            else:
                await self.db.update_one({"_id": interaction.guild.id}, {"$push": {"ignored": channel.id}})
                return await interaction.response.send_message(f"{channel.mention} has been ignored.", ephemeral=True)

    @Aoi.command(name="count", description="Set the starboard count.")
    @Aoi.describe(count="The amount of stars required to post to the starboard.")
    @Aoi.checks.has_permissions(manage_guild=True)
    async def count(self, interaction: discord.Interaction, count: Aoi.Range[int, 1, 10]):
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            return await interaction.response.send_message("Starboard is disabled.", ephemeral=True)
        else:
            await self.db.update_one({"_id": interaction.guild.id}, {"$set": {"count": count}})
            return await interaction.response.send_message(f"Starboard count has been set to {count}.", ephemeral=True)

    @Aoi.command(name="random", description="Get a random starboard message.")
    async def random(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.db.find_one({"_id": interaction.guild.id})
        if not data:
            return await interaction.followup.send("Starboard is not setup on this server.")
        msg = random.choice(data["messages"])
        for channel in interaction.guild.text_channels:
            try:
                message = await channel.fetch_message(msg['message'])
            except discord.NotFound:
                pass
        if not message:
            return await interaction.followup.send("Message not found.")
        if message.attachments:
            embeds = []
            for attachment in message.attachments:
                e = discord.Embed(
                    url="https://www.google.com/", colour=discord.Colour.gold())
                e.set_image(url=attachment.url)
                embeds.append(e)
            reactCount = 0
            for reaction in message.reactions:
                if reaction.emoji == '⭐':
                    reactCount += reaction.count
            embeds[0].set_author(
                name=message.author, icon_url=message.author.avatar.url)
            if message.content:
                embeds[0].add_field(name="Message:",
                                    value=message.content, inline=False)
            e.add_field(name="# of Stars:", value=f"⭐ {reactCount}")
            embeds[0].add_field(name="Link to Message:",
                                value=f"[Click Here]({message.jump_url})")
            embeds[0].set_footer(text=f"ID: {message.id}")
            embeds[0].timestamp = message.created_at
            return await interaction.followup.send(embeds=embeds)
        else:
            reactCount = 0
            for reaction in message.reactions:
                if reaction.emoji == '⭐':
                    reactCount += reaction.count
            e = discord.Embed(
                title="Random Starboard Message:", colour=discord.Colour.gold())
            e.set_author(name=message.author,
                         icon_url=message.author.avatar.url)
            if message.content:
                e.add_field(name="Message:",
                            value=message.content, inline=False)
            e.add_field(name="# of Stars:", value=f"⭐ {reactCount}")
            e.add_field(name="Link to Message:",
                        value=f"[Click Here]({message.jump_url})")
            if message.attachments:
                e.set_image(url=message.attachments[0].url)
            e.set_footer(text=f"ID: {message.id}")
            e.timestamp = message.created_at
            return await interaction.followup.send(embed=e)

    @random.error
    @count.error
    @toggle.error
    @ignore_channel.error
    async def starboard_error(self, interaction: discord.Interaction, error: commands.CommandError):
        self.bot.logger.error(f"[Starboard] Error: {error}")
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
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        data = await self.db.find_one({"_id": payload.guild_id})
        if data is not None:
            if data['enabled'] is True:
                if payload.channel_id in data['ignored']:
                    return
                starboard = self.bot.get_channel(data['channel'])
                channel = self.bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                reactCount = 0
                for reaction in message.reactions:
                    if reaction.emoji == '⭐':
                        reactCount += reaction.count
                if reactCount >= data['count']:
                    if message.attachments:
                        embeds = []
                        for attachment in message.attachments:
                            e = discord.Embed(
                                url="https://www.google.com/", colour=discord.Colour.gold())
                            e.set_image(url=attachment.url)
                            embeds.append(e)
                        embeds[0].set_author(
                            name=message.author, icon_url=message.author.avatar.url)
                        if message.content:
                            embeds[0].add_field(name="Message:",
                                                value=message.content, inline=False)
                        embeds[0].add_field(name="Link to Message:",
                                            value=f"[Click Here]({message.jump_url})")
                        embeds[0].set_footer(text=f"ID: {message.id}")
                        embeds[0].timestamp = message.created_at
                        for msg in data['messages']:
                            if msg['message'] == payload.message_id:
                                msg = await starboard.fetch_message(msg['starboard'])
                                return await msg.edit(embeds=embeds, content=f"⭐ {reactCount} - {message.channel.mention}")
                        msg = await starboard.send(embeds=embeds, content=f"{reactCount} ⭐ - {message.channel.mention}")
                        return await self.db.update_one({"_id": payload.guild_id}, {"$push": {"messages": {"message": message.id, "starboard": msg.id}}})
                    else:
                        e = discord.Embed(colour=discord.Colour.gold())
                        e.set_author(name=message.author,
                                     icon_url=message.author.avatar.url)
                        if message.content:
                            e.add_field(name="Message:",
                                        value=message.content, inline=False)
                        e.add_field(name="Link to Message:",
                                    value=f"[Click Here]({message.jump_url})")
                        if message.attachments:
                            e.set_image(url=message.attachments[0].url)
                        e.set_footer(text=f"ID: {message.id}")
                        e.timestamp = message.created_at
                        for msg in data['messages']:
                            if msg['message'] == payload.message_id:
                                msg = await starboard.fetch_message(msg['starboard'])
                                return await msg.edit(embed=e, content=f"{reactCount} ⭐ - {message.channel.mention}")
                        msg = await starboard.send(embed=e, content=f"{reactCount} ⭐ - {message.channel.mention}")
                        return await self.db.update_one({"_id": payload.guild_id}, {"$push": {"messages": {"message": message.id, "starboard": msg.id}}})

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        data = await self.db.find_one({"_id": payload.guild_id})
        if data is not None:
            if data['enabled'] is True:
                if payload.channel_id in data['ignored']:
                    return
                starboard = self.bot.get_channel(data['channel'])
                channel = self.bot.get_channel(payload.channel_id)
                message = await channel.fetch_message(payload.message_id)
                reactCount = 0
                for reaction in message.reactions:
                    if reaction.emoji == '⭐':
                        reactCount += reaction.count
                if reactCount >= data['count']:
                    if message.attachments:
                        embeds = []
                        for attachment in message.attachments:
                            e = discord.Embed(
                                url="https://www.google.com/", colour=discord.Colour.gold())
                            e.set_image(url=attachment.url)
                            embeds.append(e)
                        embeds[0].set_author(
                            name=message.author, icon_url=message.author.avatar.url)
                        if message.content:
                            embeds[0].add_field(name="Message:",
                                                value=message.content, inline=False)
                        embeds[0].add_field(name="Link to Message:",
                                            value=f"[Click Here]({message.jump_url})")
                        embeds[0].set_footer(text=f"ID: {message.id}")
                        embeds[0].timestamp = message.created_at
                        for msg in data['messages']:
                            if msg['message'] == payload.message_id:
                                msg = await starboard.fetch_message(msg['starboard'])
                                return await msg.edit(embeds=embeds, content=f"⭐ {reactCount} - {message.channel.mention}")
                        msg = await starboard.send(embeds=embeds, content=f"{reactCount} ⭐ - {message.channel.mention}")
                        return await self.db.update_one({"_id": payload.guild_id}, {"$push": {"messages": {"message": message.id, "starboard": msg.id}}})
                    else:
                        e = discord.Embed(colour=discord.Colour.gold())
                        e.set_author(name=message.author,
                                     icon_url=message.author.avatar.url)
                        if message.content:
                            e.add_field(name="Message:",
                                        value=message.content, inline=False)
                        e.add_field(name="Link to Message:",
                                    value=f"[Click Here]({message.jump_url})")
                        if message.attachments:
                            e.set_image(url=message.attachments[0].url)
                        e.set_footer(text=f"ID: {message.id}")
                        e.timestamp = message.created_at
                        for msg in data['messages']:
                            if msg['message'] == payload.message_id:
                                msg = await starboard.fetch_message(msg['starboard'])
                                return await msg.edit(embed=e, content=f"{reactCount} ⭐ - {message.channel.mention}")
                        msg = await starboard.send(embed=e, content=f"{reactCount} ⭐ - {message.channel.mention}")
                        return await self.db.update_one({"_id": payload.guild_id}, {"$push": {"messages": {"message": message.id, "starboard": msg.id}}})
                else:
                    for msg in data['messages']:
                        if msg['message'] == payload.message_id:
                            msg = await starboard.fetch_message(msg['starboard'])
                            return await msg.delete()
                    return await self.db.update_one({"_id": payload.guild_id}, {"$pull": {"messages": {"message": message.id}}})

    @commands.Cog.listener()
    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent):
        data = await self.db.find_one({"_id": payload.guild_id})
        if data is not None:
            if data['enabled'] is True:
                if payload.channel_id in data['ignored']:
                    return
                starboard = self.bot.get_channel(data['channel'])
                for msg in data['messages']:
                    if msg['message'] == payload.message_id:
                        ms = await starboard.fetch_message(msg['starboard'])
                        await ms.delete()
                        data['messages'].remove(msg)
                        return await self.db.update_one({"_id": payload.guild_id}, {"$set": {"messages": data['messages']}})


async def setup(bot):
    await bot.add_cog(Starboard(bot))
