import discord
from discord.ext import commands


class Mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason: str = None):
        """Kicks a member from the server."""
        try:
            await ctx.guild.kick(member, reason=reason)
            await ctx.send(f"{member.mention} has been kicked from the server.")
        except discord.Forbidden:
            await ctx.send("<:tickNo:697759586538749982> I cannot kick that member. Make sure I have the correct permissions.")

    @commands.command()
    @commands.has_permissions(ban_members=True)
    async def ban(self, ctx, member: discord.Member, *, reason: str = None):
        """Bans a member from the server."""
        try:
            await ctx.guild.ban(member, reason=reason)
            await ctx.send(f"{member.mention} has been banned from the server.")
        except discord.Forbidden:
            await ctx.send("<:tickNo:697759586538749982> I cannot ban that member. Make sure I have the correct permissions.")

    @commands.command()
    @commands.has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int):
        """Deletes a certain amount of messages."""
        try:
            await ctx.channel.purge(limit=amount)
            await ctx.send(f"{amount} messages have been deleted.")
        except discord.Forbidden:
            await ctx.send("<:tickNo:697759586538749982> I cannot delete messages. Make sure I have the correct permissions.")

    #check audit logs for the member
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def checkaudit(self, ctx, member: discord.Member):
        """Checks the audit logs for a member."""
        try:
            e = discord.Embed(color=discord.Color.blurple())
            e.title = f"{member.name}'s audit logs:"
            e.set_thumbnail(url=member.avatar)
            e.description = ""
            async for log in member.guild.audit_logs(limit=20, user=member):
                e.description += f"{log.action} - {log.reason}\n"
            await ctx.send(embed=e)
        except discord.Forbidden:
            await ctx.send("<:tickNo:697759586538749982> I cannot check the audit logs. Make sure I have the correct permissions.")

async def setup(bot):
    await bot.add_cog(Mod(bot))