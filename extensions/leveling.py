import discord
import random
import typing
from discord.ext import commands
from discord import app_commands as Aoi
from easy_pil import Editor, load_image_async, Font


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
        if member.bot:
            return await interaction.followup.send("Bots can't level up!")
        try:
            user = [e for e in data["users"] if e["_id"] == member.id][0]
            nextLvl = user['level'] * user['level'] * 100
            currentXp = user['xp']
            filter = Editor("./utils/images/filter.png").resize((900, 300))
            background = Editor(
                "./utils/images/leaderboard.png").resize(((900, 300)))
            background.paste(filter, (0, 0))
            profile_picture = await load_image_async(str(member.avatar.url))
            profile = Editor(profile_picture).resize((150, 150)).circle_image()
            poppins = Font.poppins(size=40)
            poppins_small = Font.poppins(size=30)
            background.rectangle((200, 220), width=650,
                                 height=40, color="#0a0a0a", radius=20)
            background.bar((200, 220), max_width=650, height=40, percentage=round(
                currentXp / nextLvl * 100), color="#FFFFFF", radius=20)
            background.text(
                (200, 40), f"{member.name}#{member.discriminator}", font=poppins, color="#FFFFFF")
            background.rectangle((200, 100), width=350,
                                 height=2, fill="#FFFFFF")
            background.paste(profile, (30, 30))
            background.text(
                (200, 130), f"Level - {user['level']} | XP - {user['xp']}/{user['xpCap']}", font=poppins_small, color="#FFFFFF")
            background.paste(filter, (0, 0))
            file = discord.File(fp=background.image_bytes,
                                filename="levelcard.png")
            return await interaction.followup.send(file=file)
        except IndexError:
            return await interaction.followup.send("This user doesn't have any xp!")

    @Aoi.command(name="leaderboard", description="Check the server leaderboard.")
    async def leaderboard(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Fonts
        poppins_small = Font.poppins(size=25, variant="regular")
        poppins_large = Font.poppins(size=75, variant="bold")

        # Plots
        profilePics = [(200, 200), (200, 355), (200, 525), (200, 700), (200, 875),
                       (820, 200), (820, 355), (820, 525), (820, 700), (820, 875), (1500, 200), (1500, 355), (1500, 525), (1500, 700), (1500, 875)]
        names = [(320, 200), (320, 350), (320, 530), (320, 710), (320, 880),
                 (940, 200), (940, 350), (940, 530), (940, 710), (940, 880), (1620, 200), (1620, 350), (1620, 530), (1620, 710), (1620, 880)]
        text = [(320, 230), (320, 380), (320, 560), (320, 740), (320, 910),
                (940, 230), (940, 380), (940, 560), (940, 740), (940, 910), (1620, 230), (1620, 380), (1620, 560), (1620, 740), (1620, 910)]
        bars = [(320, 270), (320, 420), (320, 600), (320, 780), (320, 950),
                (940, 270), (940, 420), (940, 600), (940, 780), (940, 950), (1620, 270), (1620, 420), (1620, 600), (1620, 780), (1620, 950)]

        data = await self.db.find_one({"_id": interaction.guild.id})
        if not data:
            return await interaction.followup.send("This server doesn't have leveling setup!")
        background = Editor(
            "./utils/images/leaderboard.png").resize(((2200, 1130)))
        filter = Editor("./utils/images/filter.png").resize((2200, 1130))
        background.paste(filter, (0, 0))
        background.paste(filter, (0, 0))
        background.text((1100, 75), f"{interaction.guild.name} Leaderboard:",
                        color="white", font=poppins_large, align="center")
        users = sorted(
            data["users"], key=lambda x: x["level"], reverse=True)[0:15]
        for index, user in enumerate(users):
            member = await interaction.guild.fetch_member(user['_id'])
            profile_picture = await load_image_async(str(member.avatar.url))
            profile = Editor(profile_picture).resize((100, 100)).circle_image()
            background.paste(profile, profilePics[index])
            background.text(names[index], f"{member.name}#{member.discriminator}", font=Font.poppins(
                size=20), color="#FFFFFF")
            background.rectangle(
                bars[index], width=400, height=20, color="#0a0a0a", radius=20)
            background.bar(bars[index], max_width=400, height=20, percentage=round(
                user['xp'] / user['xpCap'] * 100), color="#FFFFFF", radius=20)
            background.text(
                text[index], f"Level - {user['level']} | XP - {user['xp']}/{user['xpCap']}", font=poppins_small, color="#FFFFFF")
        file = discord.File(fp=background.image_bytes,
                            filename="leaderboard.png")
        return await interaction.followup.send(file=file)

    Leveling = Aoi.Group(name="leveling", description="Leveling commands!")

    @Leveling.command(name="rewards", description="Check the server rewards.")
    async def rewards(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.db.find_one({"_id": interaction.guild.id})
        if not data:
            return await interaction.followup.send("This server doesn't have leveling setup!")
        elif data['enabled'] == False:
            return await interaction.followup.send("This server doesn't have leveling enabled!")
        elif data['roles'] == []:
            return await interaction.followup.send("This server doesn't have any rewards setup!")
        e = discord.Embed(title="Leveling Rewards", color=discord.Color.teal())
        e.set_thumbnail(url=interaction.guild.icon.url)
        for role in data["roles"]:
            e.add_field(
                name=f"Level {role['level']}", value=f"{interaction.guild.get_role(role['role']).mention}", inline=False)
        return await interaction.followup.send(embed=e)

    @Leveling.command(name="config", description="Show the server's leveling config.")
    @Aoi.checks.has_permissions(manage_guild=True)
    async def config(self, interaction: discord.Interaction):
        await interaction.response.defer()
        data = await self.db.find_one({"_id": interaction.guild.id})
        if not data:
            return await interaction.followup.send("This server doesn't have leveling setup!")
        channel = self.bot.get_channel(data['channel'])
        e = discord.Embed(title="Leveling Config", color=discord.Color.teal())
        e.set_thumbnail(url=interaction.guild.icon.url)
        e.add_field(name="Leveling Enabled", value=f"{data['enabled']}")
        if channel is not None:
            e.add_field(
                name="Leveling Channel", value=f"{channel.mention}", inline=False)
        if data['ignoreChannels'] != []:
            e.add_field(
                name="Ignored Channels", value=f"{', '.join([self.bot.get_channel(channel).mention for channel in data['ignoreChannels']])}", inline=False)
        else:
            e.add_field(name="Ignored Channels", value="None", inline=False)
        if data['roles'] != []:
            e.add_field(
                name="Roles", value=f"{', '.join([interaction.guild.get_role(role['role']).mention for role in data['roles']])}", inline=False)
        else:
            e.add_field(name="Roles", value="None", inline=False)
        return await interaction.followup.send(embed=e)

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
                        "level": 1,
                        "xpCap": 100
                    })
                    return await self.db.update_one({"_id": message.guild.id}, {"$set": data})
                if user["level"] == 1:
                    user["xp"] += random.randint(5, 15)
                else:
                    user["xp"] += random.randint(15, 25)
                if user["xp"] >= user['xpCap']:
                    user["xp"] = 0
                    user["level"] += 1
                    user["xpCap"] = (user["level"] * user["level"] * 100)
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
    @rewards.error
    @config.error
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
