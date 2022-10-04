import discord
from discord.ext import commands
from discord import app_commands as Fresh


class Help(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.modules = {}
        self.commands = self.bot.tree.walk_commands()
        self.bot.remove_command('help')

    @Fresh.command(name="help")
    async def help(self, interaction: discord.Interaction, module: str = None):
        """Show's the bot's commands."""
        for command in self.commands:
            try:
                self.modules[command.module].append(command)
            except KeyError:
                self.modules[command.module] = [command]
        if not module:
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
        else:
            module = f"extensions.{module.lower()}"
            e = discord.Embed(colour=discord.Colour.teal())
            e.set_author(
                name=f"Commands for {module.split('.')[1].capitalize()}", icon_url=self.bot.user.avatar)
            e.set_thumbnail(url=self.bot.user.avatar)
            e.description = ""
            for command in self.modules[module]:
                e.description += f"`{command.name}`- {command.description}\n"
            return await interaction.response.send_message(embed=e, ephemeral=True)


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(Help(bot))
