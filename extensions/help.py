import discord
from discord.ext import commands
from discord import app_commands as Fresh


class Help(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.modules = {}
        self.bot.remove_command('help')

    async def module_auto(self, interaction: discord.Interaction, current: str):
        return [
            Fresh.Choice(name=module, value=module)
            for module in self.bot.cogs if module not in ('Jishaku', 'ErrorHandler')
        ]

    async def command_auto(self, interaction: discord.Interaction, current: str):
        return [
            Fresh.Choice(name=f"{command.name} - {command.description}",
                         value=command.name)
            for command in self.bot.tree.get_commands() if current.lower() in command.name.lower()
        ][0:25]

    @Fresh.command(name="help")
    @Fresh.autocomplete(module=module_auto, command=command_auto)
    async def help(self, interaction: discord.Interaction, module: str = None, command: str = None):
        """Get help on one of the bots commands or modules."""
        if not module and not command:
            e = discord.Embed(colour=discord.Colour.teal(),
                              description="\n".join([e.capitalize() for e in self.bot.cogs if e not in ('Jishaku', 'ErrorHandler')]))
            e.set_thumbnail(url=self.bot.user.avatar)
            e.set_author(
                name=f"{self.bot.user.name} Extensions:", icon_url=self.bot.user.avatar)
            return await interaction.response.send_message(
                embed=e
            )
        if module and not command:
            cog = self.bot.get_cog(module)
            cmds = ""
            for cmd in cog.walk_app_commands():
                params = ""
                if cmd.parameters:
                    for param in cmd.parameters:
                        params += f"<{param.name}> "
                cmds += f"`{cmd.name} {params}` - {cmd.description}\n"
            e = discord.Embed(colour=discord.Colour.teal(), description=cmds)
            e.set_author(
                name=f"Commands for {module}:", icon_url=self.bot.user.avatar)
            e.set_thumbnail(url=self.bot.user.avatar)
            return await interaction.response.send_message(embed=e)
        else:
            command = self.bot.tree.get_command(command)
            params = ""
            try:
                if command.parameters:
                    for param in command.parameters:
                        params += f"<{param.name}> "
            except AttributeError:
                pass
            if command:
                e = discord.Embed(colour=discord.Colour.teal())
                e.set_thumbnail(url=self.bot.user.avatar)
                e.add_field(name=f"{command.name} {params}",
                            value=command.description, inline=False)
                try:
                    e.add_field(name="Sub Commands:", value="\n".join(
                        [f"`{e.name}` - {e.description}" for e in command.commands]))
                except AttributeError:
                    pass
                return await interaction.response.send_message(embed=e)
            else:
                return await interaction.response.send_message(
                    content="I have failed to fetch the help for that command, please try again."
                )


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(Help(bot))
