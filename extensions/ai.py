import time
import random
import discord
import openai
import base64
import aiohttp
from io import BytesIO
from discord.ext import commands
from discord import app_commands as Aoi
from buttons.AiImagePaging import Paging


class Ai(commands.GroupCog, description="All Artificial intelligence related commands."):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.AiKey = self.bot.config['openAiKey']
        openai.api_key = self.AiKey

    @Aoi.command(name="image")
    @Aoi.describe(input="What do you want the AI to create?")
    async def image(self, interaction: discord.Interaction, input: str):
        """Create images from text with AI."""
        await interaction.response.defer()
        ETA = int(time.time() + 60)
        await interaction.followup.send(
            content=f"<a:loading:697759686509985814> Generating your images, I should be done <t:{ETA}:R>...",
        )
        async with aiohttp.request("POST", "https://backend.craiyon.com/generate", json={'prompt': input}) as response:
            r = await response.json()
            images = r['images']
            image = BytesIO(base64.decodebytes(images[0].encode("utf-8")))
            e = discord.Embed(
                colour=discord.Colour.teal(),
                description=f"{interaction.user.mention} Results are done! (Generated by craiyon.com)",
            )
            e.add_field(name="Prompt:", value=input)
            e.set_image(url="attachment://image.png")
            e.set_footer(
                text=f"Viewing image 1/{len(images)}...")
            try:
                await interaction.delete_original_response()
                view = Paging(bot=self.bot, prompt=input,
                              images=images, index=0)
                view.message = await interaction.channel.send(
                    file=discord.File(image, "image.png"),
                    embed=e,
                    view=view
                )
            except Exception as e:
                self.bot.richConsole.print(
                    f"[bold red][{interaction.command.name}][/] ERR: {str(e)}")

    @Aoi.command(name="sql")
    @Aoi.describe(input="Ex: find all users who live in California and have over 1000 credits")
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

    @Aoi.command(name="aio")
    @Aoi.describe(input="What do you want to say to Aoi?")
    async def aio(self, interaction: discord.Interaction, input: str):
        """Talk to Aoi."""
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
