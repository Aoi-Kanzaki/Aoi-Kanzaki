import discord
from discord.ext import commands
from discord import app_commands as Aoi


class Help(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.modules = {}
        self.bot.remove_command('help')

    async def module_auto(self, interaction: discord.Interaction, current: str):
        return [
            Aoi.Choice(name=module, value=module)
            for module in self.bot.cogs if current.lower() in module.lower()
            and module not in ('Jishaku', 'ErrorHandler', 'ContextMenus', 'Help')
        ]

    async def command_auto(self, interaction: discord.Interaction, current: str):
        choices = []
        for command in self.bot.tree.get_commands():
            if command.module == "extensions.contextmenus":
                continue
            else:
                choices.append(Aoi.Choice(
                    name=f"{command.name} - {command.description}", value=command.name))
                try:
                    for cmd in command.commands:
                        choices.append(Aoi.Choice(
                            name=f"{cmd.name} - {cmd.description}", value=cmd.name))
                except AttributeError:
                    pass
        return choices[0:25]

    # async def command_auto(self, interaction: discord.Interaction, current: str):
    #     return [
    #         Aoi.Choice(name=f"{command.name} - {command.description}",
    #                    value=command.name)
    #         for command in self.bot.tree.get_commands() if current.lower()
    #         in command.name.lower() and command.module != "extensions.contextmenus"
    #     ][0:25]

    @Aoi.command(name="help")
    @Aoi.autocomplete(module=module_auto, command=command_auto)
    @Aoi.describe(module="Select a module to list commands from.", command="Select a command to get help on.")
    async def help(self, interaction: discord.Interaction, module: str = None, command: str = None):
        """Get help on one of the bots commands or modules."""
        ignore_cogs = ['Jishaku', 'ErrorHandler', 'ContextMenus', 'Help']
        if not module and not command:
            e = discord.Embed(colour=discord.Colour.teal(),
                              description="\n".join([e for e in self.bot.cogs if e not in ignore_cogs]))
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
                try:
                    if cmd.parameters:
                        for param in cmd.parameters:
                            params += f"<{param.name}> "
                    cmds += f"`{cmd.name} {params}` - {cmd.description}\n"
                except AttributeError:
                    cmds += f"`{cmd.name}` - {cmd.description}\n"
            e = discord.Embed(colour=discord.Colour.teal(), description=cmds)
            e.set_author(
                name=f"Commands for {module}:", icon_url=self.bot.user.avatar)
            e.set_thumbnail(url=self.bot.user.avatar)
            return await interaction.response.send_message(embed=e)
        else:
            cmd = self.bot.tree.get_command(command)
            if not cmd:
                for cumand in self.bot.tree.get_commands():
                    try:
                        for cmmd in cumand.commands:
                            if cmmd.name == command:
                                cmd = cmmd
                    except AttributeError:
                        pass
            if cmd:
                e = discord.Embed(colour=discord.Colour.teal())
                e.set_thumbnail(url=self.bot.user.avatar)
                e.set_author(
                    name=f"Help for {cmd.name}:", icon_url=self.bot.user.avatar)
                e.description = cmd.description
                try:
                    if cmd.parameters:
                        e.add_field(name="Parameters:",
                                    value="\n".join([f"`{param.name}` - {param.description}" for param in cmd.parameters]))
                except AttributeError:
                    pass
                try:
                    e.add_field(name="Sub Commands:", value="\n".join(
                        [f"`{cmd.name}` - {cmd.description}" for cmd in cmd.commands]))
                except AttributeError:
                    pass
                return await interaction.response.send_message(embed=e)
            return await interaction.response.send_message(
                content="I have failed to fetch the help for that command, please try again."
            )

    @help.error
    async def send_error(self, interaction: discord.Interaction, error):
        self.bot.logger.error(f"[Help] Error: {error}")
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


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(Help(bot))
