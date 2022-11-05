import discord
import requests
from discord.ext import commands
from discord import app_commands as Aoi


class Crypto(commands.GroupCog, description="Crypto related commands."):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

    async def get_latest(self):
        headers = {
            'Accepts': 'application/json',
            'X-CMC_PRO_API_KEY': self.bot.config['cryptoAPIkey']
        }
        url = 'https://pro-api.coinmarketcap.com/v1/cryptocurrency/listings/latest'
        json = requests.get(url, headers=headers).json()
        return json['data']

    @Aoi.command(name="bitcoin")
    async def bitcoin(self, interaction: discord.Interaction):
        """Get Bitcoins current price."""
        try:
            latest = await self.get_latest()
            for x in latest:
                if x['symbol'] == 'BTC':
                    return await interaction.response.send_message(
                        content=f"**{x['symbol']}** is currrently sitting at **${x['quote']['USD']['price']}**"
                    )
        except Exception as e:
            self.bot.richConsole.print(
                f"[bold red][{interaction.command.name}][/] ERR: {str(e)}")
            return await interaction.response.send_message(content=f"Error: {e}")

    @Aoi.command(name="ethereum")
    async def etherium(self, interaction: discord.Interaction):
        """Get Ethereum current price."""
        try:
            latest = await self.get_latest()
            for x in latest:
                if x['symbol'] == 'ETH':
                    return await interaction.response.send_message(
                        content=f"**{x['symbol']}** is currrently sitting at **${x['quote']['USD']['price']}**"
                    )
        except Exception as e:
            self.bot.richConsole.print(
                f"[bold red][{interaction.command.name}][/] ERR: {str(e)}")
            return await interaction.response.send_message(content=f"Error: {e}")

    @Aoi.command(name="xrp")
    async def xrp(self, interaction: discord.Interaction):
        """Get XRP current price."""
        try:
            latest = await self.get_latest()
            for x in latest:
                if x['symbol'] == 'XRP':
                    return await interaction.response.send_message(
                        content=f"**{x['symbol']}** is currrently sitting at **${x['quote']['USD']['price']}**"
                    )
        except Exception as e:
            self.bot.richConsole.print(
                f"[bold red][{interaction.command.name}][/] ERR: {str(e)}")
            return await interaction.response.send_message(content=f"Error: {e}")

    @bitcoin.error
    @etherium.error
    @xrp.error
    async def send_error(self, interaction: discord.Interaction, error):
        e = discord.Embed(title="An Error has Occurred!",
                          colour=discord.Colour.red())
        e.add_field(name="Error:", value=error)
        try:
            await interaction.response.send_message(embed=e)
        except:
            await interaction.followup.send(embed=e)


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(Crypto(bot))
