import os
import random
import discord
import openai
from discord.ext import commands
from discord import app_commands as Fresh


class Ai(commands.GroupCog, name="ai", description="All Artificial intelligence related commands."):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.AiKey = self.bot.config['openAiKey']
        openai.api_key = self.AiKey

    @Fresh.command(name="sql")
    @Fresh.describe(input="Ex: find all users who live in California and have over 1000 credits")
    async def sql(self, interaction: discord.Interaction, input: str):
        """Create simple SQL queries."""
        response = openai.Completion.create(
            model="text-davinci-002",
            prompt=input,
            temperature=0.3,
            max_tokens=60,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        e = discord.Embed(colour=discord.Colour.teal(),
                          title="Here are your choices:")
        number = 1
        for choice in response['choices']:
            e.add_field(name=f"Choice {number}:", value="```\n{}```".format(
                str(choice['text']).replace('\n\n', '')))
        return await interaction.response.send_message(
            embed=e,
            ephemeral=True
        )

    @Fresh.command(name="fresh")
    @Fresh.describe(input="What do you want to say to Fresh?")
    async def fresh(self, interaction: discord.Interaction, input: str):
        """Talk to Fresh."""
        response = openai.Completion.create(
            model="text-davinci-002",
            prompt=input,
            temperature=0.5,
            max_tokens=60,
            top_p=0.3,
            frequency_penalty=0.5,
            presence_penalty=0.0
        )
        choice = random.choice(response['choices'])
        text = choice['text']
        return await interaction.response.send_message(
            content=str(text).replace('\n\n', ''),
            ephemeral=True
        )


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(Ai(bot))
