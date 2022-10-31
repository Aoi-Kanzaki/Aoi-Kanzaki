import time
import discord
from discord.ext import commands


class ContextMenus(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot

        @bot.tree.context_menu(name="Userinfo")
        async def userinfo(interaction: discord.Interaction, user: discord.Member):
            roles = ", ".join(
                [f"<@&{x.id}>" for x in sorted(user.roles, key=lambda x: x.position,
                                               reverse=True) if x.id != interaction.guild.default_role.id]
            ) if len(user.roles) > 1 else "None"

            e = discord.Embed(colour=user.top_role.color.value)
            e.set_thumbnail(url=user.avatar.url)
            e.add_field(name="Name:", value=user)
            e.add_field(name="Nickname", value=user.nick if hasattr(
                user, "nick") else "None")
            e.add_field(name="ID", value=user.id)
            e.add_field(name=f"Roles ({len(user.roles)-1})",
                        value=roles, inline=False)
            e.add_field(name="Created Account",
                        value=f"<t:{str(time.mktime(user.created_at.timetuple())).split('.')[0]}:R>")
            e.add_field(name="Joined this server",
                        value=f"<t:{str(time.mktime(user.joined_at.timetuple())).split('.')[0]}:R>")

            usr = await interaction.client.fetch_user(user.id)
            if usr.banner:
                e.set_image(url=usr.banner.url)
            return await interaction.response.send_message(embed=e)


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(ContextMenus(bot))
