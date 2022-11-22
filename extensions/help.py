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
        return [
            Aoi.Choice(
                name=f"{command.name} - {command.description}", value=command.name) for command in self.bot.tree.get_commands()
            if current.lower() in command.name.lower() and command.module not in ('extensions.help', 'extensions.contextmenus')
        ][0:10]

    @Aoi.command(name="help")
    @Aoi.autocomplete(module=module_auto, command=command_auto)
    @Aoi.describe(module="Select a module to list commands from.", command="Select a command to get help on.")
    async def help(self, interaction: discord.Interaction, module: str = None, command: str = None):
        """Get help on one of the bots commands or modules."""
        ignore_cogs = ['Jishaku', 'ContextMenus', 'Help']
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
            cmds = ""
            for cmd in await self.bot.tree.fetch_commands():
                cmd2 = self.bot.tree.get_command(cmd.name)
                if cmd2 is not None:
                    if str(cmd2.module).split('.')[1] == module.lower():
                        try:
                            if cmd2.parameters != []:
                                params = " ".join(
                                    [f"<{param.name}>" for param in cmd2.parameters])
                                cmds += f"{cmd.mention} `{params}` - {cmd2.description}\n"
                            else:
                                cmds += f"{cmd.mention} - {cmd2.description}\n"
                        except AttributeError:
                            cmds += f"{cmd.mention} - {cmd2.description}\n"
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
                        [f"</{cmd.parent.name} {cmd.name}:{self.bot.user.id}> - {cmd.description}" for cmd in cmd.commands]))
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
