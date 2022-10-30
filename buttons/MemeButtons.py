import json
import urllib
import discord


class MemeButtons(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)

    @discord.ui.button(label="Next", style=discord.ButtonStyle.success)
    async def next(self, interaction: discord.Interaction, button: discord.ui.Button):
        memeApi = urllib.request.urlopen(
            "https://meme-api.herokuapp.com/gimme")
        memeData = json.load(memeApi)
        memeUrl = memeData["url"]
        memeName = memeData["title"]
        memeAuthor = memeData["author"]
        memeSub = memeData["subreddit"]
        memeLink = memeData["postLink"]
        e = discord.Embed(title=memeName)
        e.set_image(url=memeUrl)
        e.set_footer(
            text=f"Meme By: {memeAuthor} | Subreddit: {memeSub} | Post: {memeLink}")
        return await interaction.response.edit_message(embed=e)

    @discord.ui.button(label="Done", style=discord.ButtonStyle.danger)
    async def done(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.message.delete()
