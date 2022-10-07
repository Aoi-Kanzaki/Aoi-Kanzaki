import discord
from discord.ext import commands
from discord import app_commands as Fresh


class Help(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.modules = {}
        self.bot.remove_command('help')
        self.commands = self.bot.tree.walk_commands()

    async def module_auto(self, interaction: discord.Interaction, current: str):
        for command in self.commands:
            try:
                self.modules[command.module].append(command)
            except KeyError:
                self.modules[command.module] = [command]
        return [
            Fresh.Choice(name=str(module.replace('extensions.', '')).capitalize(),
                         value=module.replace('extensions.', ''))
            for module in self.modules.keys() if current.lower() in module.lower()
        ]

    async def command_auto(self, interaction: discord.Interaction, current: str):
        return [
            Fresh.Choice(name=f"{command.name} - {command.description}",
                         value=str(command.name).capitalize())
            for command in self.bot.tree.walk_commands() if current.lower() in command.name.lower()
        ][0:25]

    @Fresh.command(name="help")
    @Fresh.autocomplete(module=module_auto, command=command_auto)
    async def help(self, interaction: discord.Interaction, module: str = None, command: str = None):
        """Show's the bot's commands."""
        try:
            for comnd in self.commands:
                try:
                    self.modules[comnd.module].append(comnd)
                except KeyError:
                    self.modules[comnd.module] = [comnd]
            if not module and not command:
                extensions = ""
                number = 1
                for key in self.modules.keys():
                    extensions += f"`{number}` {key.split('.')[1].capitalize()}\n"
                    number += 1
                e = discord.Embed(colour=discord.Colour.teal(),
                                  description=extensions)
                e.set_author(
                    name=f"{self.bot.user.name} Extensions:", icon_url=self.bot.user.avatar)
                e.set_thumbnail(url=self.bot.user.avatar)
                return await interaction.response.send_message(embed=e, ephemeral=True)
            if module and not command:
                module = f"extensions.{module.lower()}"
                e = discord.Embed(colour=discord.Colour.teal())
                e.set_author(
                    name=f"Commands for {module.split('.')[1].capitalize()}", icon_url=self.bot.user.avatar)
                e.set_thumbnail(url=self.bot.user.avatar)
                e.description = ""
                for command in self.modules[module]:
                    e.description += f"`{command.name}`- {command.description}\n"
                return await interaction.response.send_message(embed=e, ephemeral=True)
            else:
                command = self.bot.tree.get_command(command.lower())
                e = discord.Embed(colour=discord.Colour.teal())
                e.description = f"{command.description}"
                return await interaction.response.send_message(embed=e, ephemeral=True)
        except Exception as e:
            print(e)


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(Help(bot))
