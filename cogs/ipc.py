from typing import Dict
from discord.ext import commands, ipc
from discord.ext.ipc.server import Server
from discord.ext.ipc.errors import IPCError
from discord.ext.ipc.objects import ClientPayload

class Routes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        if not hasattr(bot, "ipc"):
            bot.ipc = ipc.Server(self.bot, secret_key=self.bot.config['secret_key'])
    
    async def cog_load(self) -> None:
        await self.bot.ipc.start()

    async def cog_unload(self) -> None:
        await self.bot.ipc.stop()
        self.bot.ipc = None

    @Server.route()
    async def get_user_data(self, data: ClientPayload) -> Dict:
        user = self.bot.get_user(data.user_id)
        return user._to_minimal_user_json()

    @Server.route()
    async def get_guild_count(self, data: ClientPayload) -> Dict:
        return {"total": len(self.bot.guilds)}

    @Server.route()
    async def get_guild_ids(self, data: ClientPayload) -> Dict:
        final = []
        for guild in self.bot.guilds:
            final.append(guild.id)
        return {"guilds": final}

    @Server.route()
    async def get_guild(self, data):
        guild = self.bot.get_guild(data.guild_id)
        if guild is None:
            return None
        guild_data = {
            "name": guild.name,
            "id": guild.id,
            "prefix" : "?"
        }
        return guild_data

async def setup(bot):
    await bot.add_cog(Routes(bot))