import discord
from discord.ext import commands

class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot  = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.MissingRequiredArgument):
            a = discord.Embed(colour=0x36393E)
            a.set_author(name=f"{ctx.command.name} {ctx.command.signature}", icon_url=self.bot.user.avatar)
            a.description = f"{ctx.command.help}"
            await ctx.send(embed=a)
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send("<:tickNo:697759586538749982> You don't have permissions to execute this command.", delete_after=5)
        elif isinstance(error, commands.BadArgument):
            a = discord.Embed(colour=0x36393E)
            a.set_author(name=f"{ctx.command.name} {ctx.command.signature}", icon_url=self.bot.user.avatar)
            a.description = f"{ctx.command.help}"
            await ctx.send(embed=a)
        elif isinstance(error, commands.CommandOnCooldown):
            seconds = error.retry_after
            seconds = round(seconds, 2)
            await ctx.send(f'<:tickNo:697759586538749982> Mate slow the fuck down. {seconds}s remaining.', delete_after=seconds)
        elif isinstance(error, commands.NoPrivateMessage):
            await ctx.send('<:tickNo:697759586538749982> Mate you can\'t use that command in DMS, please invite me to a server or go to one I\'m in.', delete_after=10)
        elif isinstance(error, discord.Forbidden):
            await ctx.send("<:tickNo:697759586538749982> I dont have permissions to execute this command.", delete_after=5)
        else:
            if ctx.command:
                print(error)

async def setup(bot):
    await bot.add_cog(ErrorHandler(bot))