import re
import time
import discord
import aiohttp
from discord.ext import commands

url_rx = re.compile(r'https?:\/\/(?:www\.)?.+')


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

        @bot.tree.context_menu(name="Favorite Songs")
        async def fav_songs_context(interaction: discord.Interaction, member: discord.Member):
            """Show's a users favorite songs."""
            data = await self.bot.db.favorites.find_one({"_id": member.id})
            if data is None:
                return await interaction.response.send_message(
                    f"<:tickNo:697759586538749982> **{member.display_name}** doesn't have any favorite songs!")
            else:
                e = discord.Embed(colour=discord.Colour.teal())
                e.set_author(
                    icon_url=member.display_avatar,
                    name=f"{member.display_name}'s Favorite Songs:"
                )
                e.description = ""
                number = 1
                for song in data['songs'][0:5]:
                    if not url_rx.match(song):
                        song = f'spsearch:{song}'
                    try:
                        result = await self.bot.lavalink.get_tracks(song, check_local=True)
                    except:
                        return await interaction.response.send_message(
                            "The music module is not enabled! Or I have encountered a more serious error.", ephemeral=True)
                    e.description += f"`{number}.` {result['tracks'][0]['title']}\n"
                    number += 1
                if len(data['songs']) > 5:
                    total = len(data['songs']) - 5
                    e.description += f"\nNot showing **{total}** more songs..."
                return await interaction.response.send_message(embed=e)

        @fav_songs_context.error
        @activities.error
        @userinfo.error
        async def send_error(interaction: discord.Interaction, error):
            self.bot.logger.error(f"[Context Menus] Error: {error}")
            if isinstance(error, commands.MissingPermissions):
                return await interaction.response.send_message("You do not have the required permissions to use this command!", ephemeral=True)
            if isinstance(error, commands.MissingRequiredArgument):
                return await interaction.response.send_message("You are missing a required argument!", ephemeral=True)
            if isinstance(error, commands.BadArgument):
                return await interaction.response.send_message("You provided an invalid argument!", ephemeral=True)
            if isinstance(error, commands.CommandInvokeError):
                return await interaction.response.send_message("An error occurred while running this command!", ephemeral=True)
            else:
                e = discord.Embed(title="An Error has Occurred!",
                                  colour=discord.Colour.red())
                e.add_field(name="Error:", value=error)
                try:
                    await interaction.response.send_message(embed=e)
                except:
                    await interaction.followup.send(embed=e)
                async with aiohttp.ClientSession() as session:
                    webhook = discord.Webhook.from_url(
                        url=self.bot.config['webhooks']['mainlogs'], session=session)
                    await webhook.send(embed=e)


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(ContextMenus(bot))
