async def is_owner(ctx):
    if ctx.author.id == 827940585201205258:
        return True
    else:
        await ctx.send("Command is locked to developers, sorry.", delete_after=10)
        return False


async def check_commands(ctx):
    if ctx.author.bot:
        return
    if ctx.guild is None:
        await ctx.send(
            "<:tickNo:697759586538749982> You cannot use commands in DMs. Please use the commands in a server."
        )
        return False
    return True
