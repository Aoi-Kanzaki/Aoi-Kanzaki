import discord
import aiosqlite
from discord.ext import commands
from easy_pil import Editor, Canvas, load_image_async, Font


class Levels(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(aliases=["lvl", "rank"])
    async def level(self, ctx, member: discord.Member = None):
        """Show's your current level."""
        await ctx.typing()
        if member is None:
            member = ctx.author
        async with aiosqlite.connect("./data/level.db") as db:
            levelsys = await db.execute("SELECT levelsys FROM levelSettings WHERE guild = ?", (ctx.guild.id,))
            levelsys = await levelsys.fetchone()
            if levelsys:
                if not levelsys[0] == 1:
                    return await ctx.send("The leveling system is not enabled in this server!")
            xp = await db.execute("SELECT xp FROM levels WHERE user = ? AND guild = ?", (member.id, ctx.guild.id,))
            xp = await xp.fetchone()
            xpcap = await db.execute("SELECT xpcap FROM levels WHERE user = ? AND guild = ?", (member.id, ctx.guild.id,))
            xpcap = await xpcap.fetchone()
            level = await db.execute("SELECT level FROM levels WHERE user = ? AND guild = ?", (member.id, ctx.guild.id,))
            level = await level.fetchone()
            if not xp or not level:
                await db.execute("INSERT INTO levels (level, xp, xpcap, user, guild) VALUES (?, ?, ?, ?, ?)", (0, 0, 1000, member.id, ctx.guild.id,))
                await db.commit()
            try:
                xp = xp[0]
                level = level[0]
                xpcap = xpcap[0]
            except TypeError:
                xp = 0
                level = 0
                xpcap = 1000
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
            await ctx.send(file=file)

    @commands.hybrid_group()
    async def slvl(self, ctx):
        """Leveling system settings."""
        if ctx.invoked_subcommand is None or isinstance(ctx.invoked_subcommand, commands.Group):
            await self.bot.send_sub_help(ctx, ctx.command)

    @slvl.command(aliases=["e", "en"])
    @commands.has_permissions(manage_guild=True)
    async def enable(self, ctx):
        """Enables the leveling system."""
        async with aiosqlite.connect("./data/level.db") as db:
            levelsys = await db.execute("SELECT levelsys FROM levelSettings WHERE guild = ?", (ctx.guild.id,))
            levelsys = await levelsys.fetchone()
            if levelsys:
                if levelsys[0]:
                    return await ctx.send("The leveling system is already enabled.")
                await db.execute("UPDATE levelSettings SET levelsys = ? WHERE guild = ?", (True, ctx.guild.id,))
            await db.execute("INSERT INTO levelSettings VALUES (?, ?, ?, ?)", (True, 0, 0, ctx.guild.id, ))
            await ctx.send("Enabled the leveling system.")
            await db.commit()

    @slvl.command(aliases=["d", "di"])
    @commands.has_permissions(manage_guild=True)
    async def disable(self, ctx):
        """Disables the leveling system."""
        async with aiosqlite.connect("./data/level.db") as db:
            levelsys = await db.execute("SELECT levelsys FROM levelSettings WHERE guild = ?", (ctx.guild.id,))
            levelsys = await levelsys.fetchone()
            if levelsys:
                if not levelsys[0]:
                    return await ctx.send("The leveling system is already disabled.")
                await db.execute("UPDATE levelSettings SET levelsys = ? WHERE guild = ?", (False, ctx.guild.id,))
            await db.execute("INSERT INTO levelSettings VALUES (?, ?, ?, ?)", (False, 0, 0, ctx.guild.id,))
            await ctx.send("Disabled the leveling system.")
            await db.commit()

    @slvl.command()
    async def rewards(self, ctx):
        """Shows the current leveling rewards."""
        async with aiosqlite.connect("./data/level.db") as db:
            levelsys = await db.execute("SELECT levelsys FROM levelSettings WHERE guild = ?", (ctx.guild.id,))
            levelsys = await levelsys.fetchone()
            if levelsys:
                if not levelsys[0] == 1:
                    return await ctx.send("The leveling system is not enabled in this server!")
            roles = await db.execute("SELECT * FROM levelSettings WHERE guild = ?", (ctx.guild.id,))
            roleLevels = await roles.fetchall()
            if not roleLevels:
                return await ctx.send("No role levels have been setup for this guild!")
            e = discord.Embed(title="Role Levels:", description="Role levels for this server.")
            for role in roleLevels:
                e.add_field(name=f"Level {role[2]}", value=f"{ctx.guild.get_role(role[1])}", inline=False)
            await ctx.send(embed=e)

    @slvl.command(aliases=["sr", "addrole", "ar"])
    @commands.has_permissions(manage_guild=True)
    async def setrole(self, ctx, level: int, *, role: discord.Role):
        """Add a role to the leveling rewards."""
        async with aiosqlite.connect("./data/level.db") as db:
            levelsys = await db.execute("SELECT levelsys FROM levelSettings WHERE guild = ?", (ctx.guild.id,))
            levelsys = await levelsys.fetchone()
            if levelsys:
                if not levelsys[0] == 1:
                    return await ctx.send("The leveling system is not enabled in this server!")
            get_role = await db.execute("SELECT role FROM levelSettings WHERE role = ? AND guild = ?", (role.id, ctx.guild.id,))
            roleTF = await get_role.fetchone()
            get_level = await db.execute("SELECT role FROM levelSettings WHERE levelreq = ? AND guild = ?", (level, ctx.guild.id,))
            levelTF = await get_level.fetchone()
            if roleTF or levelTF:
                return await ctx.send("A role or level setting for that value already exists.")
            await db.execute("INSERT INTO levelSettings VALUES (?, ?, ?, ?)", (True, role.id, level, ctx.guild.id,))
            await db.commit()
            await ctx.send("Updated that level role.")

    @slvl.command(aliases=["lb"])
    async def leaderboard(self, ctx):
        """Shows the current leveling leaderboard for the guild."""
        await ctx.typing()
        async with aiosqlite.connect("./data/level.db") as db:
            levelsys = await db.execute("SELECT levelsys FROM levelSettings WHERE guild = ?", (ctx.guild.id,))
            levelsys = await levelsys.fetchone()
            if levelsys:
                if not levelsys[0] == 1:
                    return await ctx.send("The leveling system is not enabled in this server!")
            get_data = await db.execute("SELECT level, xp, user FROM levels WHERE guild = ? ORDER BY level DESC, xp DESC LIMIT 10", (ctx.guild.id,))
            data = await get_data.fetchall()
            if data:
                e = discord.Embed(title="Leveling Leaderboard:")
                count = 0
                for table in data:
                    count += 1
                    user = ctx.guild.get_member(table[2])
                    e.add_field(name=f"{count}. {user.name}", value=f"Level-**{table[0]}** | XP-**{table[1]}**", inline=False)
                return await ctx.send(embed=e)
            return await ctx.send("There are no users stored in this guild.")


async def setup(bot):
    await bot.add_cog(Levels(bot))
