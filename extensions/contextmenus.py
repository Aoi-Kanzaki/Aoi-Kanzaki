import time
import discord
from discord.ext import commands


class ContextMenus(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        bot = bot

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

        @bot.tree.context_menu(name="Activities")
        async def activities(interaction: discord.Interaction, member: discord.Member):
            await interaction.response.defer()
            embeds = []

            member = member or interaction.user
            member = member.guild.get_member(member.id)

            if member.activities != None:
                for activity in member.activities:
                    if isinstance(activity, discord.Spotify):
                        e = discord.Embed(
                            title="Listening to Spotify",
                            colour=activity.color
                        )
                        e.description = f"**Title:** {activity.title}\n"
                        e.description += f"**Artist:** {activity.artist}\n"
                        e.description += f"**Album:** {activity.album}"
                        e.set_thumbnail(url=activity.album_cover_url)
                        embeds.append(e)
                    elif isinstance(activity, discord.Activity):
                        e = discord.Embed(
                            title=f"{activity.name}",
                            colour=discord.Colour.blurple()
                        )
                        if activity.details:
                            e.description = f"{activity.details}"
                        if activity.large_image_url:
                            e.set_thumbnail(url=activity.large_image_url)
                        embeds.append(e)
                    elif isinstance(activity, discord.CustomActivity):
                        e = discord.Embed(
                            colour=discord.Colour.blurple(),
                            description=activity.name
                        )
                        embeds.append(e)
                    elif isinstance(activity, discord.Streaming):
                        e = discord.Embed(
                            colour=discord.Colour.purple(),
                            title="Currently Streaming"
                        )
                        e.description = f"**Platform:** {activity.platform}\n"
                        e.description += f"**Name:** {activity.name}\n"
                        e.description += f"**Game:** {activity.game}\n"
                        e.description += f"Come watch here! [Go to {activity.platform}]({activity.url})"
                        embeds.append(e)
                    elif isinstance(activity, discord.Game):
                        e = discord.Embed(
                            colour=discord.Colour.blurple(),
                            description=activity.name
                        )
                        embeds.append(e)

                return await interaction.followup.send(embeds=embeds, content=f"**{member}'s Activities:**")

            return await interaction.followup.send("Nothing found.")


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(ContextMenus(bot))
