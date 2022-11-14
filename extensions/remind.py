import re
import discord
from datetime import timedelta, datetime
from discord.ext import commands, tasks
from discord import app_commands as Aoi
from humanfriendly import format_timespan

UNITS = {'s': 'seconds', 'm': 'minutes',
         'h': 'hours', 'd': 'days', 'w': 'weeks'}


def convert_to_seconds(s):
    return int(timedelta(**{
        UNITS.get(m.group('unit').lower(), 'seconds'): float(m.group('val'))
        for m in re.finditer(r'(?P<val>\d+(\.\d+)?)(?P<unit>[smhdw]?)', s, flags=re.I)
    }).total_seconds())


class Remind(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.db = self.bot.db.reminders
        self.check_reminders.start()

    @Aoi.command(name="remind", description="Remind yourself of something.")
    async def remind(self, interaction: discord.Interaction, time: str, *, reminder: str):
        """Remind yourself of something.

        Time is a string ending in [s|m|h|d|w] for seconds, minutes, hours, days, or weeks.

        Example: `remind 1h30m Do something in 1 hour and 30 minutes.`"""
        data = await self.db.find_one({"_id": interaction.user.id})
        if data is None:
            data = {"_id": interaction.user.id, "reminders": []}
            await self.db.insert_one(data)

        time = convert_to_seconds(time)
        seconds = format_timespan(time)
        await self.db.update_one({"_id": interaction.user.id}, {"$push": {"reminders": {"channel": interaction.channel.id, "time": datetime.now(), "duration": time, "reminder": reminder}}})
        await interaction.response.send_message("Reminder set! I'll remind you in {}.".format(seconds))

    @Aoi.command(name="reminders", description="List your reminders.")
    async def reminders(self, interaction: discord.Interaction):
        """List your reminders."""
        data = await self.db.find_one({"_id": interaction.user.id})
        print(data)
        if data is None:
            return await interaction.response.send_message("You have no reminders set.")

        reminders = data["reminders"]
        if not reminders:
            return await interaction.response.send_message("You have no reminders set.")

        embed = discord.Embed(title="Reminders", color=discord.Color.teal())
        embed.description = "\n".join(
            [f"**{format_timespan(reminder['time'])}** - {reminder['reminder']}" for reminder in reminders])
        await interaction.response.send_message(embed=embed)

    @Aoi.command(name="remind-delete", description="Delete a reminder.")
    async def remind_delete(self, interaction: discord.Interaction, reminder: str):
        """Delete a reminder."""
        data = await self.db.find_one({"_id": interaction.user.id})
        if data is None:
            return await interaction.response.send_message("You have no reminders set.")

        reminders = data["reminders"]
        if not reminders:
            return await interaction.response.send_message("You have no reminders set.")

        for i, r in enumerate(reminders):
            if r["reminder"] == reminder:
                del reminders[i]
                await self.db.update_one({"_id": interaction.user.id}, {"$set": {"reminders": reminders}})
                return await interaction.response.send_message("Reminder deleted.")

        await interaction.response.send_message("Reminder not found.")

    @tasks.loop(seconds=5)
    async def check_reminders(self):
        async for user in self.db.find({}):
            if user['reminders'] is not []:
                for reminder in user['reminders']:
                    currentTime = datetime.now()
                    if currentTime >= reminder['time'] + timedelta(seconds=reminder['duration']):
                        e = discord.Embed(
                            title="Reminder", description=reminder['reminder'], color=discord.Color.teal())
                        e.set_footer(text="Reminder set at")
                        e.timestamp = reminder['time']
                        try:
                            await self.bot.get_user(user['_id']).send(embed=e)
                        except discord.Forbidden:
                            channel = self.bot.get_channel(reminder['channel'])
                            await channel.send(f"<@{user['_id']}>", embed=e)
                        user['reminders'].remove(reminder)
                        await self.db.update_one({"_id": user['_id']}, {"$set": {"reminders": user['reminders']}})
                        self.bot.richConsole.print(
                            f"[bold green][Reminders][/] Sent reminder to {user['_id']}")

    @remind.error
    @reminders.error
    @remind_delete.error
    async def send_error(self, interaction: discord.Interaction, error):
        self.bot.logger.error(f"[Spotify] Error: {error}")
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


async def setup(bot: commands.AutoShardedBot):
    await bot.add_cog(Remind(bot))
