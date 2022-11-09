import discord
import random
import typing
import time
import prettytable
from discord.ext import commands
from discord import app_commands as Aoi


class Leveling(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db.levels

    @Aoi.command(name="rank", description="Check your rank.")
    async def rank(self, interaction: discord.Interaction, member: discord.Member = None):
        await interaction.response.defer()
        member = member or interaction.user
        data = await self.db.find_one({"_id": interaction.guild.id})
        if not data:
            return await interaction.followup.send("This server doesn't have leveling setup!")
        if data['enabled'] == False:
            return await interaction.followup.send("This server doesn't have leveling enabled!")
        user = [e for e in data["users"] if e["_id"] == member.id]
        try:
            user = user[0]
        except IndexError:
            user = {
                "_id": member.id,
                "xp": 0,
                "level": 0,
                "xpCap": 1000
            }
            await self.db.update_one({"_id": member.id}, {"$push": {"users": user}}, upsert=True)
        e = discord.Embed(
            colour=discord.Colour.teal(),
            title=f"{member}'s Level",
            description=f"Level: {user['level']}\nXP: {user['xp']}/{user['xpCap']}"
        )
        e.set_thumbnail(url=member.avatar.url)
        await interaction.followup.send(embed=e)

    @Aoi.command(name="leaderboard", description="Check the server leaderboard.")
    async def leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.db.find_one({"_id": interaction.guild.id})
        if not data:
            return await interaction.followup.send(
                "This server doesn't have leveling setup!", ephemeral=True
            )
        if data['enabled'] == False:
            return await interaction.followup.send(
                "This server doesn't have leveling enabled!", ephemeral=True
            )
        users = sorted(data["users"], key=lambda x: x["xp"], reverse=True)
        table = prettytable.PrettyTable(align='r')
        table.field_names = ["Rank", "User", "Level", "XP"]
        index = 1
        for user in users:
            table.add_row([index, interaction.guild.get_member(user['_id']).name, user['level'],
                           f"{user['xp']}/{user['xpCap']}"])
            index += 1
        e = discord.Embed(
            colour=discord.Colour.teal(),
            description=f"```{table}```"
        )
        e.set_author(name=f"{interaction.guild.name} Leaderboard:",
                     icon_url=interaction.guild.icon.url)
        e.set_thumbnail(url=interaction.guild.icon.url)
        e.set_footer(text=f"Requested by {interaction.user.name}",
                     icon_url=interaction.user.avatar.url)
        await interaction.followup.send(embed=e)

    Leveling = Aoi.Group(name="leveling", description="Leveling commands!")

    @Leveling.command(name="toggle", description="Toggle leveling on or off.")
    @Aoi.checks.has_permissions(manage_guild=True)
    async def toggle(self, interaction: discord.Interaction, toggle: typing.Literal["enable", "disable"]):
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            data = {
                "_id": interaction.guild.id,
                "channel": None,
                "enabled": False,
                "ignoreChannels": [],
                "roles": [],
                "users": []
            }
            await self.db.insert_one(data)
        if toggle == "enable":
            if data["enabled"]:
                return await interaction.response.send_message("Leveling is already enabled!", ephemeral=True)
            data["enabled"] = True
            await interaction.response.send_message("Leveling has been enabled!", ephemeral=True)
        else:
            if not data["enabled"]:
                return await interaction.response.send_message("Leveling is already disabled!", ephemeral=True)
            data["enabled"] = False
            await interaction.response.send_message("Leveling has been disabled!", ephemeral=True)
        await self.db.update_one({"_id": interaction.guild.id}, {"$set": data})

    @Leveling.command(name="ignore-channel", description="Ignore a channel for leveling.")
    @Aoi.checks.has_permissions(manage_guild=True)
    async def ignore_channel(self, interaction: discord.Interaction, channel: discord.TextChannel):
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            data = {
                "_id": interaction.guild.id,
                "channel": None,
                "enabled": False,
                "ignoreChannels": [],
                "roles": [],
                "users": []
            }
            await self.db.insert_one(data)
        if channel.id in data["ignoreChannels"]:
            data["ignoreChannels"].remove(channel.id)
            await interaction.response.send_message(f"{channel.mention} is no longer ignored!", ephemeral=True)
        else:
            data["ignoreChannels"].append(channel.id)
            await interaction.response.send_message(f"{channel.mention} is now ignored!", ephemeral=True)
        await self.db.update_one({"_id": interaction.guild.id}, {"$set": data})

    @Leveling.command(name="channel", description="Set the leveling channel.")
    @Aoi.checks.has_permissions(manage_guild=True)
    async def channel(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            data = {
                "_id": interaction.guild.id,
                "channel": None,
                "enabled": False,
                "ignoreChannels": [],
                "roles": [],
                "users": []
            }
            await self.db.insert_one(data)
        if channel is None:
            data["channel"] = None
            await interaction.response.send_message("Leveling channel has been reset!", ephemeral=True)
        else:
            if data["channel"] == channel.id:
                return await interaction.response.send_message("Leveling channel is already set to that channel!", ephemeral=True)
            data["channel"] = channel.id
            await interaction.response.send_message(f"Leveling channel has been set to {channel.mention}!", ephemeral=True)
        await self.db.update_one({"_id": interaction.guild.id}, {"$set": data})

    @Leveling.command(name="add-role", description="Add a role to the leveling system.")
    @Aoi.checks.has_permissions(manage_guild=True)
    async def add_role(self, interaction: discord.Interaction, rolename: str, level: int):
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            data = {
                "_id": interaction.guild.id,
                "channel": None,
                "enabled": False,
                "ignoreChannels": [],
                "roles": [],
                "users": []
            }
            await self.db.insert_one(data)
        role = await interaction.guild.create_role(name=rolename, reason="Added to Leveling system.")
        data["roles"].append({
            "role": role.id,
            "level": level
        })
        await interaction.response.send_message(f"Added {role.mention} to the leveling system!", ephemeral=True)
        await self.db.update_one({"_id": interaction.guild.id}, {"$set": data})

    @Leveling.command(name="remove-role", description="Remove a role from the leveling system.")
    @Aoi.checks.has_permissions(manage_guild=True)
    async def remove_role(self, interaction: discord.Interaction, role: discord.Role):
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            data = {
                "_id": interaction.guild.id,
                "channel": None,
                "enabled": False,
                "ignoreChannels": [],
                "roles": [],
                "users": []
            }
            await self.db.insert_one(data)
        data["roles"] = [e for e in data["roles"] if e["role"] != role.id]
        await interaction.response.send_message(f"Removed {role.mention} from the leveling system!", ephemeral=True)
        await self.db.update_one({"_id": interaction.guild.id}, {"$set": data})
        await role.delete(reason="Removed from leveling system.")

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return
        if message.guild is None:
            return
        data = await self.db.find_one({"_id": message.guild.id})
        if data is None:
            data = {
                "_id": message.guild.id,
                "channel": None,
                "enabled": False,
                "ignoreChannels": [],
                "roles": [],
                "users": []
            }
            return await self.db.insert_one(data)
        if not data["enabled"]:
            return
        else:
            if message.channel.id in data["ignoreChannels"]:
                return
            else:
                user = [e for e in data["users"]
                        if e["_id"] == message.author.id]
                try:
                    user = user[0]
                except IndexError:
                    data["users"].append({
                        "_id": message.author.id,
                        "xp": 0,
                        "level": 0,
                        "xpCap": 1000
                    })
                    return await self.db.update_one({"_id": message.guild.id}, {"$set": data})
                user["xp"] += random.randint(15, 25)
                if user["xp"] >= user['xpCap']:
                    user["xp"] = 0
                    user["level"] += 1
                    user["xpCap"] += 1000
                    if data["channel"] is not None:
                        channel = self.bot.get_channel(data["channel"])
                        if channel is not None:
                            await channel.send(f"{message.author.mention} has leveled up to level {user['level']}!")
                    else:
                        await message.channel.send(f"{message.author.mention} has leveled up to level {user['level']}!")
                    for role in data["roles"]:
                        if role["level"] == user["level"]:
                            await message.author.add_roles(message.guild.get_role(role["role"]))
                await self.db.update_one({"_id": message.guild.id}, {"$set": data})

    @remove_role.error
    @add_role.error
    @channel.error
    @ignore_channel.error
    @toggle.error
    @leaderboard.error
    @rank.error
    async def send_error(self, interaction: discord.Interaction, error):
        self.bot.logger.error(f"[Leveling] Error: {error}")
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


async def setup(bot):
    await bot.add_cog(Leveling(bot))
