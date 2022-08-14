import discord
from discord.ext import commands


class HelpSelect(discord.ui.Select):
    def __init__(self, bot):
        self.bot = bot
        options = []
        ignore_cogs = [
            "Jishaku",
            "Help",
            "Leveling",
            "ErrorHandler",
            "JoinMsg",
            "MusicChannel",
        ]
        emotes = ["1⃣", "2⃣", "3⃣", "4⃣", "5⃣", "6⃣", "7⃣", "8⃣", "9⃣", "🔟"]
        number = 0
        for cog in self.bot.cogs:
            if cog in ignore_cogs:
                continue
            options.append(discord.SelectOption(label=f"{cog}", emoji=emotes[number]))
            number += 1
        super().__init__(
            placeholder="Select a module...",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: discord.Interaction):
        cog = self.bot.get_cog(self.values[0])
        if cog:
            msg = ""
            for command in cog.walk_commands():
                if command.hidden:
                    pass
                elif command.parent:
                    pass
                else:
                    msg += f"`{command.name}` - {command.short_doc}\n"
            e = discord.Embed(
                title=f"{cog.qualified_name} Commands:",
                colour=discord.Colour.blurple(),
                description=msg,
            )
            e.set_thumbnail(url=self.bot.user.avatar)
            await interaction.response.edit_message(embed=e)


class HelpView(discord.ui.View):
    def __init__(self, bot):
        self.bot = bot
        super().__init__(timeout=60)
        self.add_item(HelpSelect(self.bot))


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command()
    async def help(self, ctx, *, option: str = None):
        """Just your basic help command."""
        ignore_cogs = ["Jishaku", "Help", "Leveling", "ErrorHandler"]
        group_commands = ["jsk", "jsk voice"]
        if option is not None:
            if option in group_commands:
                return await self.bot.send_sub_help(ctx, self.bot.get_command(option))
            cog = self.bot.get_cog(option)
            if cog:
                msg = ""
                for command in cog.walk_commands():
                    if command.hidden:
                        pass
                    elif command.parent:
                        pass
                    else:
                        msg += f"`{command.name}` - {command.short_doc}\n"
                e = discord.Embed(
                    title=f"Command help for cog {cog.qualified_name}:",
                    colour=discord.Colour.blurple(),
                    description=msg,
                )
                e.set_thumbnail(url=self.bot.user.avatar)
                return await ctx.send(embed=e)
            else:
                command = self.bot.get_command(option)
                if command:
                    e = discord.Embed(colour=discord.Colour.blurple())
                    e.set_author(
                        name=f"{command.name} {command.signature}",
                        icon_url=self.bot.user.avatar,
                    )
                    e.description = f"{command.help}"
                    return await ctx.send(embed=e)
        else:
            e = discord.Embed(colour=discord.Colour.blurple())
            e.description = "For help on a certain module select one from the dropdown below. Or you can use the following command below.\n\n"
            e.description += (
                f"`{ctx.prefix}help <command>` for more info on a specific command."
            )
            e.set_author(
                name=f"{self.bot.user.name} Help", icon_url=self.bot.user.avatar
            )
            e.set_image(url="https://cdn.upload.systems/uploads/UCbzyCAS.jpg")
            view = HelpView(self.bot)
            return await ctx.send(embed=e, view=view)


async def setup(bot):
    bot.remove_command("help")
    await bot.add_cog(Help(bot))
