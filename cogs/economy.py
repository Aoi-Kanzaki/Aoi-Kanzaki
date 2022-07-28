import discord
import aiosqlite
import random
from colr import color
from discord.ext import commands

class Economy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):
        async with aiosqlite.connect("./data/bank.db") as db:
            await db.execute("CREATE TABLE IF NOT EXISTS bank (wallet INTEGER, bank INTEGER, maxbank INTEGER, user INTEGER)")
            await db.execute("CREATE TABLE IF NOT EXISTS inv (laptop INTEGER, phone INTEGER, fakeid INTEGER, user INTEGER)")
            await db.execute("CREATE TABLE IF NOT EXISTS shop (name TEXT, id TEXT, desc TEXT, cost INTEGER)")
            await db.commit()
        print(color("The Economy cog is ready!", fore=self.bot.colors['blue']))

    async def create_balance(self, user):
        async with aiosqlite.connect("./data/bank.db") as db:
            await db.execute("INSERT INTO bank VALUES (?, ?, ?, ?)", (0, 100, 500, user.id,))
            await db.commit()
            return

    async def create_inv(self, user):
        async with aiosqlite.connect("./data/bank.db") as db:
            await db.execute("INSERT INTO inv VALUES (?, ?, ?, ?)", (0, 0, 0, user.id,))
            await db.commit()
            return

    async def get_inv(self, user):
        async with aiosqlite.connect("./data/bank.db") as db:
            get_data = await db.execute("SELECT laptop, phone, fakeid FROM inv WHERE user = ?", (user.id,))
            data = await get_data.fetchone()
            if data is None:
                await self.create_inv(user)
                return 0, 0, 0
            laptop, phone, fakeid = data[0], data[1], data[2]
            return laptop, phone, fakeid

    async def get_balance(self, user):
        async with aiosqlite.connect("./data/bank.db") as db:
            get_data = await db.execute("SELECT wallet, bank, maxbank FROM bank WHERE user = ?", (user.id,))
            data = await get_data.fetchone()
            if data is None:
                await self.create_balance(user)
                return 0, 100, 500
            wallet, bank, maxbank = data[0], data[1], data[2]
            return wallet, bank, maxbank

    async def update_wallet(self, user, amount: int):
        async with aiosqlite.connect("./data/bank.db") as db:
            get_wallet = await db.execute("SELECT wallet FROM bank WHERE user = ?", (user.id,))
            wallet = await get_wallet.fetchone()
            if wallet is None:
                await self.create_balance(user)
                return 0
            await db.execute("UPDATE bank SET wallet = ? WHERE user = ?", (wallet[0] + amount, user.id,))
            await db.commit()

    async def update_bank(self, user, amount):
        async with aiosqlite.connect("./data/bank.db") as db:
            get_bank = await db.execute("SELECT wallet, bank, maxbank FROM bank WHERE user = ?", (user.id,))
            bank = await get_bank.fetchone()
            if bank is None:
                await self.create_balance(user)
                return 0
            capacity = int(bank[2] - bank[1])
            if amount > capacity:
                await self.update_wallet(user, amount)
                return 1
            await db.execute("UPDATE bank SET bank = ? WHERE user = ?", (bank[1] + amount, user.id,))
            await db.commit()

    async def update_maxbank(self, user, amount):
        async with aiosqlite.connect("./data/bank.db") as db:
            get_maxbank = await db.execute("SELECT maxbank FROM bank WHERE user = ?", (user.id,))
            maxbank = await get_maxbank.fetchone()
            if maxbank is None:
                await self.create_balance(user)
                return 0
            await db.execute("UPDATE bank SET maxbank = ? WHERE user = ?", (maxbank[0] + amount, user.id,))
            await db.commit()
            return

    async def update_shop(name: str, id: str, desc: str, cost: int):
        async with aiosqlite.connect("./data/bank.db") as db:
            await db.execute("INSERT INTO shop VALUES (?, ?, ?, ?)", (name, id, desc, cost,))
            await db.commit()
            return

    @commands.command()
    async def balance(self, ctx, member: discord.Member=None):
        """Shows your banks balance."""
        if not member:
            member = ctx.author
        wallet, bank, maxbank = await self.get_balance(member)
        e = discord.Embed(title=f"{member.name}'s Balance:")
        e.add_field(name="Wallet", value=wallet)
        e.add_field(name="Bank", value=f"{bank}/{maxbank}")
        e.set_thumbnail(url=member.avatar)
        await ctx.send(embed=e)

    @commands.command()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def beg(self, ctx):
        """Beg for money."""
        chances = random.randint(1, 10)
        if chances == 1:
            return await ctx.send("You got nothing!")
        amount = random.randint(200, 2000)
        res = await self.update_wallet(ctx.author, amount)
        if res == 0:
            return await ctx.send("No account found so one was created for you. Please run the command again!")
        await ctx.send(f"You got **{amount}** coins!")

    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def withdraw(self, ctx, amount):
        """Widthdraw coins from your bank."""
        wallet, bank, maxbank = await self.get_balance(ctx.author)
        try:
            amount = int(amount)
        except ValueError:
            pass
        if type(amount) == str:
            if amount.lower() == "max" or amount.lower() == "all":
                amount = int(bank)
        else:
            amount = int(amount)
        bank_res = await self.update_bank(ctx.author, -amount)
        wallet_res = await self.update_wallet(ctx.author, amount)
        if bank_res == 0 or wallet_res == 0:
            return await ctx.send("No account found so one was created for you. Please run the command again!")
        wallet, bank, maxbank = await self.get_balance(ctx.author)
        e = discord.Embed(title=f"{amount} coins have been withdrew")
        e.add_field(name="New Wallet", value=wallet)
        e.add_field(name="New Bank", value=f"{bank}/{maxbank}")
        e.set_thumbnail(url=ctx.author.avatar)
        await ctx.send(embed=e)
        
    @commands.command()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def deposit(self, ctx, amount):
        """Deposit coins to your bank."""
        wallet, bank, maxbank = await self.get_balance(ctx.author)
        try:
            amount = int(amount)
        except ValueError:
            pass
        if type(amount) == str:
            if amount.lower() == "max" or amount.lower() == "all":
                amount = int(wallet)
        else:
            amount = int(amount)
        bank_res = await self.update_bank(ctx.author, amount)
        wallet_res = await self.update_wallet(ctx.author, -amount)
        if bank_res == 0 or wallet_res == 0:
            return await ctx.send("No account found so one was created for you. Please run the command again!")
        elif bank_res == 1:
            return await ctx.send("You don't have enough storage in your bank!")
        wallet, bank, maxbank = await self.get_balance(ctx.author)
        e = discord.Embed(title=f"{amount} coins have been withdrew")
        e.add_field(name="New Wallet", value=wallet)
        e.add_field(name="New Bank", value=f"{bank}/{maxbank}")
        e.set_thumbnail(url=ctx.author.avatar)
        await ctx.send(embed=e)
        
    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def give(self, ctx, member: discord.Member, amount):
        """Give a user some coins."""
        wallet, bank, maxbank = await self.get_balance(ctx.author)
        try:
            amount = int(amount)
        except ValueError:
            pass
        if type(amount) == str:
            if amount.lower() == "max" or amount.lower() == "all":
                amount = int(wallet)
        else:
            amount = int(amount)
        wallet_res = await self.update_wallet(ctx.author, -amount)
        wallet_res2 = await self.update_wallet(member, amount)
        if wallet_res == 0 or wallet_res2 == 0:
            return await ctx.send("No account found so one was created for of you. Please run the command again!")
        wallet2, bank2, maxbank2 = await self.get_balance(member)
        wallet, bank, maxbank = await self.get_balance(ctx.author)
        e = discord.Embed(title=f"Gave {amount} coins to {member.name}")
        e.add_field(name=f"{ctx.author.name}'s Wallet", value=wallet)
        e.add_field(name=f"{member.name}'s Wallet", value=wallet2)
        e.set_thumbnail(url=ctx.author.avatar)
        await ctx.send(embed=e)

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def gamble(self, ctx, amount:int=200):
        """Gamble against the odds."""
        wallet, bank, maxbank = await self.get_balance(ctx.author)
        if wallet < 200:
            return await ctx.send("You need to have at least 100 coins in your wallet!")
        if amount > wallet:
            return await ctx.send("You don't have enough coins in your wallet!")
        user_strikes = random.randint(1, 20)
        bot_strikes = random.randint(5, 20)
        e = discord.Embed()
        if user_strikes > bot_strikes:
            percentage = random.randint(50, 100)
            amount_won = int(amount*(percentage/100))
            await self.update_wallet(ctx.author, +amount_won)
            e.description = f"You won **{amount_won}** coins!\nPercentage: {percentage}\nNew Balance: `{wallet + amount_won}`"
            e.set_author(name=ctx.author.name, icon_url=ctx.author.avatar)
            e.color = discord.Color.green()
        elif bot_strikes > user_strikes:
            await self.update_wallet(ctx.author, -amount)
            e.description = f"You lost **{amount}** coins!\nNew Balance: `{wallet - amount}`"
            e.set_author(name=ctx.author.name, icon_url=ctx.author.avatar)
            e.color = discord.Color.red()
        else:
            e.description = f"It was a tie!"
            e.set_author(name=f"Shit Play {ctx.author.name}!", icon_url=ctx.author.avatar)
        e.add_field(name=f"{ctx.author.name.title()}", value=f"Strikes {user_strikes}")
        e.add_field(name=f"{ctx.bot.user.name}", value=f"Strikes {bot_strikes}")
        e.set_thumbnail(url=ctx.author.avatar)
        return await ctx.send(embed=e)

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def slots(self, ctx, amount:int=200):
        """Play the slot machine."""
        wallet, bank, maxbank = await self.get_balance(ctx.author)
        if wallet < 200:
            return await ctx.send("You need to have at least 100 coins in your wallet!")
        if amount > wallet:
            return await ctx.send("You don't have enough coins in your wallet!")
        times_factors = random.randint(1, 5)
        earnings = int(amount*times_factors)
        final = []
        for i in range(3):
            a = random.choice(['🍉', '💎', '💰'])
            final.append(a)
        if final[0] == final[1] or final[0] == final[2] or final[2] == final[0]:
            await self.update_wallet(ctx.author, +earnings)
            e = discord.Embed(color=discord.Color.green())
            e.title = f"You won {earnings} coins!\n"
            e.add_field(name="Outcome:", value=f"{final[0]}{final[1]}{final[2]}", inline=False)
            e.add_field(name="Multiplier:", value=f"X{times_factors}")
            e.add_field(name="New Balance:", value=f"{wallet+earnings}")
            e.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/1055/1055823.png")
            return await ctx.send(embed=e)
        else:
            await self.update_wallet(ctx.author, -amount)
            e = discord.Embed(color=discord.Color.red())
            e.title = f"You lost {amount} coins!\n\n"
            e.add_field(name="Outcome:", value=f"{final[0]}{final[1]}{final[2]}")
            e.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/1055/1055823.png")
            return await ctx.send(embed=e)

async def setup(bot):
    await bot.add_cog(Economy(bot))