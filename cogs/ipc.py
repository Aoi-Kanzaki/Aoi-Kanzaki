import re
from typing import Dict
from discord.ext import commands, ipc
from discord.ext.ipc.server import Server
from discord.ext.ipc.errors import IPCError
from discord.ext.ipc.objects import ClientPayload

url_rx = re.compile(r'https?:\/\/(?:www\.)?.+')

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
    async def get_guild(self, data: ClientPayload) -> Dict:
        guild = self.bot.get_guild(data.guild_id)
        if guild is None:
            return None
        guild_data = {
            "name": guild.name,
            "id": guild.id,
            "prefix" : "?"
        }
        return guild_data

    @Server.route()
    async def get_favorites(self, data: ClientPayload) -> Dict:
        favs = self.bot.db.favorites.find_one({"_id": data.user_id})
        final = []
        if favs is None:
            return {"songs": None}
        else:
            try:
                lavalink = self.bot.lavalink
            except AttributeError:
                return {"songs": ["Lavalink is unavaliable!"]}
            number = 1
            for song in favs['songs'][0:6]:
                if not url_rx.match(song):
                    song = f'spsearch:{song}'
                result = await lavalink.get_tracks(song, check_local=True)
                final.append(result['tracks'][0]['title'])
                number += 1
            if len(favs['songs']) > 6:
                total = len(favs['songs']) - 6
                final.append(f"...Not showing {total} more songs")
            return {"songs": final}

    @Server.route()
    async def get_spotify(self, data: ClientPayload) -> Dict:
        account = self.bot.db.spotifyOauth.find_one({"_id": data.user_id})
        if account is None:
            return None
        else:
            return {"account": "It is connected"}

async def setup(bot):
    await bot.add_cog(Routes(bot))