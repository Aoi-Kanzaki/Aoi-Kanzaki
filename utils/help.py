import discord
from discord.ext import commands

class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def help(self, ctx, *, option: str=None):
        """Just your basic help command."""
        ignore_cogs = ['Jishaku', 'Help', 'Leveling', 'ErrorHandler']
        group_commands = ['jsk', 'jsk voice']
        if option is not None:
            if option in group_commands:
                return await self.bot.send_sub_help(ctx, self.bot.get_command(option))
            cog = self.bot.get_cog(option)
            if cog:
                msg = ""
                for command in cog.walk_commands():
                    msg += f"`{command.name}` - {command.short_doc}\n"
                e = discord.Embed(title=f"Command help for cog {cog.qualified_name}:", colour=discord.Colour.blurple(), description=msg)
                e.set_thumbnail(url=self.bot.user.avatar)
                return await ctx.send(embed=e)
            else:
                command = self.bot.get_command(option)
                if command:
                    e = discord.Embed(colour=discord.Colour.blurple())
                    e.set_author(name=f"{command.name} {command.signature}", icon_url=self.bot.user.avatar)
                    e.description = f"{command.help}"
                    return await ctx.send(embed=e)
        else:
            msg = ""
            number = 1
            ignore_cogs = ['Jishaku', 'Help', 'Leveling', 'ErrorHandler', 'JoinMsg']
            for cog in self.bot.cogs:
                if cog in ignore_cogs:
                    pass
                else:
                    msg += f"`{number}.` {cog}\n"
                    number +=1
            e = discord.Embed(title=f"Cog help for F.res.h:", colour=discord.Colour.blurple(), description=msg)
            e.set_thumbnail(url=self.bot.user.avatar)
            return await ctx.send(embed=e)

async def setup(bot):
    bot.remove_command("help")
    await bot.add_cog(Help(bot))