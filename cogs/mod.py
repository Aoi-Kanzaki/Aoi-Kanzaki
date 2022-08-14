from ast import alias
import discord
import aiosqlite
from colr import color
from discord.ext import commands


class Mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        async with aiosqlite.connect("./data/prefixes.db") as db:
            await db.execute(
                "CREATE TABLE IF NOT EXISTS prefixs (prefix STRING, guild INTEGER)"
            )
            await db.commit()

    @commands.hybrid_command(name="prefix", aliases=["setprefix"])
    @commands.has_permissions(administrator=True)
    async def prefix(self, ctx, prefix):
        """Set the prefix for the bot."""
        async with aiosqlite.connect("./data/prefixes.db") as db:
            getData = await db.execute(
                "SELECT * FROM prefixs WHERE guild = ?", (ctx.guild.id,)
            )
            data = await getData.fetchone()
            if data is None:
                await db.execute(
                    "INSERT INTO prefixs VALUES (?, ?)", (prefix, ctx.guild.id)
                )
                await ctx.send(
                    f"<:tickYes:697759553626046546> Prefix set to `{prefix}`"
                )
            else:
                await db.execute(
                    "UPDATE prefixs SET prefix = ? WHERE guild = ?",
                    (prefix, ctx.guild.id),
                )
                await ctx.send(
                    f"<:tickYes:697759553626046546> Prefix set to `{prefix}`"
                )
            await db.commit()

    @commands.hybrid_command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        """Kicks a member from the server."""
        try:
            await ctx.guild.kick(member, reason=reason)
            await ctx.send(
                f"<:tickYes:697759553626046546> {member.mention} has been kicked from the server.",
                delete_after=5,
            )
        except discord.Forbidden:
            await ctx.send(
                "<:tickNo:697759586538749982> I cannot kick that member. Make sure I have the correct permissions."
            )

    @commands.hybrid_command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = None):
        """Bans a member from the server."""
        try:
            await ctx.guild.ban(member, reason=reason)
            await ctx.send(
                f"<:tickYes:697759553626046546> {member.mention} has been banned from the server.",
                delete_after=5,
            )
        except discord.Forbidden:
            await ctx.send(
                "<:tickNo:697759586538749982> I cannot ban that member. Make sure I have the correct permissions."
            )

    @commands.hybrid_command()
    @commands.has_permissions(manage_messages=True)
    async def purgeall(self, ctx, amount: int = 100):
        """Deletes messages from all users in a channel"""

        def is_not_bot(m):
            return not m.author.bot

        try:
            await ctx.channel.purge(limit=amount, check=is_not_bot)
        except discord.HTTPException:
            await ctx.send("The bot is missing permissions to delete messages.")

    @commands.hybrid_command()
    @commands.has_permissions(manage_messages=True)
    async def purgebots(self, ctx, amount: int = 100):
        """Deletes messages from bots in a channel"""

        def is_bot(m):
            return m.author.bot

        try:
            await ctx.channel.purge(limit=amount, check=is_bot)
        except discord.HTTPException:
            await ctx.send("The bot is missing permissions to delete messages.")


async def setup(bot):
    await bot.add_cog(Mod(bot))
