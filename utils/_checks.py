async def is_owner(ctx):
    if ctx.author.id == 827940585201205258:
        return True
    else:
        await ctx.send("Command is locked to developers, sorry.", delete_after=10)
        return False