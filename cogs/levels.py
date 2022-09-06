import random
import discord
from discord.ext import commands
from discord import app_commands as Fresh
from easy_pil import Editor, Canvas, load_image_async, Font

class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db.levels

    @Fresh.command(name="togglelevels")
    @commands.has_permissions(manage_guild=True)
    async def levels_toggle(self, interaction: discord.Interaction):
        """Enable or disable the leveling system."""
        data = self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            self.db.insert_one({
                "_id": interaction.guild.id,
                "toggle": True,
                "rewards": {},
                "users": {}
            })
            return await interaction.response.send_message(f"{interaction.guild.name} has enabled levels!")
        else:
            if data['toggle']:
                data['toggle'] = False
                self.db.update_one({"_id": interaction.guild.id}, {"$set": data})
                return await interaction.response.send_message(f"{interaction.guild.name} has disabled levels!")
            else:
                data['toggle'] = True
                self.db.update_one({"_id": interaction.guild.id}, {"$set": data})
                return await interaction.response.send_message(f"{interaction.guild.name} has enabled levels!")

    @Fresh.command(name="rank")
    async def rank(self, interaction: discord.Interaction, member: discord.Member=None):
        """Show's your current rank in the guild."""
        data = self.db.find_one({"_id": interaction.guild.id})
        if data != None and data["toggle"] != False:
            if member is None: member = interaction.user
            try:
                data = data['users'][str(member.id)]
            except KeyError:
                lvldata = {"level": 0, "xp": 0, "xpcap": 1000}
                self.db.update_one({"_id": interaction.guild.id}, {"$set": {"users": {str(member.id): lvldata}}})
                return await interaction.response.send_message(
                            f"{member.mention} You don't have a rank! But I just added you to the database!")
            if data:
                level = data['level']
                xp = data['xp']
                xpcap = data['xpcap']
                background = Editor(Canvas((900, 300), color="#141414"))
                profile_picture = await load_image_async(str(member.avatar.url))
                profile = Editor(profile_picture).resize((150, 150)).circle_image()
                poppins = Font.poppins(size=40)
                poppins_small = Font.poppins(size=30)
                card_right_shape = [(600, 0), (750, 300), (900, 300), (900, 0)]
                background.polygon(card_right_shape, color="#FFFFFF")
                background.paste(profile, (30, 30))
                background.rectangle((30, 220), width=650, height=40, color="#FFFFFF", radius=20)
                background.bar((30, 220), max_width=650, height=40, percentage=round(xp / xpcap * 100), color="#282828", radius=20)
                background.text((200, 40), f"{member.name}#{member.discriminator}", font=poppins, color="#FFFFFF")
                background.rectangle((200, 100), width=350, height=2, fill="#FFFFFF")
                background.text((200, 130), f"Level - {level} | XP - {xp}/{xpcap}", font=poppins_small, color="#FFFFFF")
                file = discord.File(fp=background.image_bytes, filename="levelcard.png")
                await interaction.response.send_message(file=file)
        else:
            return await interaction.response.send_message(
                        f"<:tickNo:697759586538749982> Leveing is disabled in this server!", ephemeral=True)

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or message.guild is None: return
        data = self.db.find_one({"_id": message.guild.id})
        if data != None and data['toggle'] != False:
            try:
                data = data['users'][str(message.author.id)]
            except KeyError:
                lvldata = {"level": 0, "xp": 0, "xpcap": 1000}
                return self.db.update_one({"_id": message.guild.id}, {"$set": {"users": {str(message.author.id): lvldata}}})
            if data:
                level = data['level']
                xp = data['xp']
                xpcap = data['xpcap']
                xp += round(random.randint(1, 30) * 1.5)
                if xp >= xpcap:
                    level += 1
                    xp = 0
                    xpcap = round(xpcap * 1.25)
                    await message.channel.send(f"{message.author.mention} has leveled up to **{level}**!")
                lvldata = {"level": level, "xp": xp, "xpcap": xpcap}
                self.db.update_one({"_id": message.guild.id}, {"$set": {"users": {str(message.author.id): lvldata}}})
            else:
                lvldata = {"level": 0, "xp": 0, "xpcap": 100}
                self.db.update_one({"_id": message.guild.id}, {"$set": {"users": {str(message.author.id): lvldata}}})

async def setup(bot):
    await bot.add_cog(Levels(bot))