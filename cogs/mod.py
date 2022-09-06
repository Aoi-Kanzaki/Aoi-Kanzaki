import discord
from discord.ext import commands
from discord import app_commands as Fresh

class Mod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @Fresh.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, interaction: discord.Interaction, user: discord.Member, reason: str=None):
        """Kicks a member from the server."""
        try:
            await interaction.guild.kick(user, reason=reason)
            await interaction.response.send_message(
                f"<:tickYes:697759553626046546> **{user.name}** has been kicked from the server.")
        except discord.Forbidden:
            await interaction.response.send_message(
                "<:tickNo:697759586538749982> I cannot kick that member. Make sure I have the correct permissions.")

    @Fresh.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(self, interaction: discord.Interaction, user: discord.Member, reason: str=None):
        """Bans a member from the server."""
        try:
            await interaction.guild.ban(user, reason=reason)
            await interaction.response.send_message(
                f"<:tickYes:697759553626046546> **{user.name}** has been banned from the server.")
        except discord.Forbidden:
            await interaction.response.send_message(
                "<:tickNo:697759586538749982> I cannot ban that member. Make sure I have the correct permissions.")
            
    @Fresh.command(name="purge")
    @commands.has_permissions(manage_messages=True)
    async def purge(self, interaction: discord.Interaction, amount: int=100):
        """Deletes messages from all users in a channel"""
        try:
            await interaction.channel.purge(limit=amount)
        except discord.HTTPException:
            await interaction.response.send_message("The bot is missing permissions to delete messages.")
        
    @Fresh.command(name="purgebots")
    @commands.has_permissions(manage_messages=True)
    async def purgebots(self, interaction: discord.Interaction, amount: int=100):
        """Deletes messages from bots in a channel"""
        def is_bot(m):
            return m.author.bot
        try:
            await interaction.channel.purge(limit=amount, check=is_bot)
        except discord.HTTPException:
            await interaction.response.send_message("The bot is missing permissions to delete messages.")

async def setup(bot):
    await bot.add_cog(Mod(bot))