from email import message
from shutil import ExecError
import discord
from discord.ext import commands
from discord import app_commands as Fresh


class Moderation(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @Fresh.command(name="ban")
    @Fresh.checks.has_permissions(ban_members=True)
    @Fresh.describe(
        member="The member you would like to ban.",
        reason="The reason why you are banning the user.",
        messages="The amount of days you want to delete messages from (0-7)."
    )
    async def ban(self, interaction: discord.Interaction, member: discord.Member, reason: str = None, messages: int = 0):
        """Ban's a user from the guild."""
        try:
            if reason is None:
                reason = "No reason provided."
            if messages > 7:
                messages = 7
            elif messages < 0:
                messages = 0
            e = discord.Embed(colour=discord.Colour.teal())
            e.description = f"You have been banned from **{interaction.guild.name}!**\n"
            e.description += f"Reason: {reason}"
            await member.send(embed=e)
            await interaction.guild.ban(user=member, reason=reason, delete_message_days=messages)
            return await interaction.response.send_message(
                content=f"{member} has been banned from the guild!",
                ephemeral=True
            )
        except discord.Forbidden:
            return await interaction.response.send_message(
                content="I cannot ban this user!",
                ephemeral=True
            )
        except discord.NotFound:
            return await interaction.response.send_message(
                content="The user was not found??",
                ephemeral=True
            )
        except Exception as e:
            return await interaction.response.send_message(
                content=e,
                ephemeral=True
            )

    @Fresh.command(name="kick")
    @Fresh.checks.has_permissions(kick_members=True)
    @Fresh.describe(
        member="The member you would like to kick.",
        reason="The reason why you are kicking the user."
    )
    async def kick(self, interaction: discord.Interaction, member: discord.Member, reason: str = None):
        """Kick's a user from the guild."""
        try:
            if reason is None:
                reason = "No reason provided."
            e = discord.Embed(colour=discord.Colour.teal())
            e.description = f"You have been kicked from **{interaction.guild.name}!**\n"
            e.description += f"Reason: {reason}"
            await member.send(embed=e)
            await interaction.guild.kick(user=member, reason=reason)
            return await interaction.response.send_message(
                content=f"{member} has been kicked from the guild!",
                ephemeral=True
            )
        except discord.Forbidden:
            return await interaction.response.send_message(
                content="I cannot kick this user!",
                ephemeral=True
            )
        except discord.NotFound:
            return await interaction.response.send_message(
                content="The user was not found??",
                ephemeral=True
            )
        except Exception as e:
            return await interaction.response.send_message(
                content=e,
                ephemeral=True
            )

    @Fresh.command(name="purge")
    @Fresh.checks.has_permissions(manage_messages=True)
    @Fresh.describe(
        amount="The amount of messages you want to delete.",
        member="The member you want to delete message from."
    )
    async def purge(self, interaction: discord.Interaction, member: discord.Member = None, amount: int = 100):
        """Purges message from the channel."""
        await interaction.response.defer(ephemeral=True)
        try:
            if member:
                def check(m):
                    return m.author == member
                deleted = await interaction.channel.purge(limit=amount, check=check)
                return await interaction.followup.send(f"I have deleted {len(deleted)} messages from {member}!")
            else:
                deleted = await interaction.channel.purge(limit=amount, bulk=True)
                return await interaction.followup.send(f"Deleted {len(deleted)} messages!")
        except discord.Forbidden:
            return await interaction.followup.send("I cannot delete messages in this channel!")
        except Exception as e:
            return await interaction.followup.send(e)

    @Fresh.command(name="cleanup")
    async def cleanup(self, interaction: discord.Interaction, amount: int = 100):
        """Cleans up the bots messages."""
        await interaction.response.defer(ephemeral=True)

        def check(m):
            return m.author == interaction.guild.me
        try:
            deleted = await interaction.channel.purge(limit=amount, check=check)
            return await interaction.followup.send(f"I have cleaned up {len(deleted)} messages!")
        except Exception as e:
            return await interaction.followup.send(e)


async def setup(bot: commands.Bot):
    await bot.add_cog(Moderation(bot))