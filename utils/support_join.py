from easy_pil import Editor, Canvas, load_image_async, Font
import discord
from discord.ext import commands

class JoinMsg(commands.Cog):
    def __init(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        if member.guild.id == 678226695190347797:
            channel = await member.guild.fetch_channel(685706016343719966)
            background = Editor(Canvas((900, 300), color="#141414"))
            try:
                profile_picture = await load_image_async(str(member.avatar.url))
            except:
                profile_picture = await load_image_async(str(member.default_avatar.url))
            profile = Editor(profile_picture).resize((150, 150)).circle_image()
            card_right_shape = [(600, 0), (750, 300), (900, 300), (900, 0)]
            background.polygon(card_right_shape, color="#2d1c20")
            background.paste(profile, (30, 70))
            background.text((220, 80), f"{member.name} Welcome to {member.guild.name}!", font=Font.poppins(size=32), color="#FFFFFF")
            background.text((270, 180), f"You are the {len(member.guild.members)}th user to join!", font=Font.poppins(size=35), color="#FFFFFF")
            file = discord.File(fp=background.image_bytes, filename="levelcard.png")
            await channel.send(file=file)

    @commands.command()
    async def jointest(self, ctx):
        channel = await ctx.guild.fetch_channel(685706016343719966)
        background = Editor(Canvas((900, 300), color="#141414"))
        profile_picture = await load_image_async(str(ctx.author.avatar.url))
        profile = Editor(profile_picture).resize((150, 150)).circle_image()
        card_right_shape = [(600, 0), (750, 300), (900, 300), (900, 0)]
        background.polygon(card_right_shape, color="#2d1c20")
        background.paste(profile, (30, 70))
        background.text((220, 80), f"{ctx.author.name} Welcome to {ctx.guild.name}!", font=Font.poppins(size=32), color="#FFFFFF")
        background.text((270, 180), f"You are the {len(ctx.guild.members)}th user to join!", font=Font.poppins(size=35), color="#FFFFFF")
        file = discord.File(fp=background.image_bytes, filename="levelcard.png")
        await channel.send(file=file)

async def setup(bot):
    await bot.add_cog(JoinMsg(bot))
