import discord
import aiosqlite
import random
import datetime
import asyncio
from colr import color
from discord.ext import commands

class Economy(commands.Cog):
    def __init__(self, bot):
        fresh = bot.tree
        self.bot = bot
        self.daily_cooldowns = {}
        self.db = self.bot.db.economy

        @fresh.command(name="daily")
        async def daily(interaction: discord.Interaction):
            """Recieve your daily coins."""
            if interaction.user.id in self.daily_cooldowns:
                difference = (datetime.datetime.now() - self.daily_cooldowns[interaction.user.id]).total_seconds()
                m, s = divmod(int(86400 - difference), 60)
                h, m = divmod(m, 60)
                if h > 0:
                    return await interaction.response.send_message(
                        f"You already claimed your daily coins! You can claim again in **{h} hour(s) {m} minute(s) {s} second(s).**")
                elif m > 0:
                    return await interaction.response.send_message(
                        f"You already claimed your daily coins! You can claim again in **{m} minute(s) {s} second(s).**")
                else:
                    return await interaction.response.send(
                        f"You already claimed your daily coins! You can claim again in **{s} second(s).**")
            wallet, bank, maxbank = await self.get_balance(interaction.user)
            await self.update_wallet(interaction.user, +5000)
            self.daily_cooldowns[interaction.user.id] = datetime.datetime.now()
            return await interaction.response.send_message(
                f"You received 5000 coins! New Balance: **{wallet+5000}**")

        @fresh.command(name="balance")
        @commands.cooldown(1, 5, commands.BucketType.user)
        async def balance(interaction: discord.Interaction, member: discord.Member=None):
            """Shows your banks balance."""
            if not member:
                member = interaction.user
            wallet, bank, maxbank = await self.get_balance(member)
            e = discord.Embed(title=f"{member.name}'s Balance:")
            e.add_field(name="Wallet", value=wallet)
            e.add_field(name="Bank", value=f"{bank}/{maxbank}")
            e.set_thumbnail(url=member.avatar)
            await interaction.response.send_message(embed=e)

        @fresh.command(name="beg")
        @commands.cooldown(1, 300, commands.BucketType.user)
        async def beg(interaction: discord.Interaction):
            """Beg for money."""
            chances = random.randint(1, 10)
            if chances == 1:
                return await interaction.response.send_message("You got nothing!")
            amount = random.randint(200, 2000)
            res = await self.update_wallet(interaction.user, +amount)
            if res == 0:
                return await interaction.response.send_message(
                    "No account found so one was created for you. Please run the command again!")
            await interaction.response.send_message(f"You got **{amount}** coins!")

        @fresh.command(name="withdraw")
        @commands.cooldown(1, 5, commands.BucketType.user)
        async def withdraw(interaction: discord.Interaction, amount: int):
            """Widthdraw coins from your bank."""
            wallet, bank, maxbank = await self.get_balance(interaction.user)
            try:
                amount = int(amount)
            except ValueError:
                pass
            if type(amount) == str:
                if amount.lower() == "max" or amount.lower() == "all":
                    amount = int(bank)
            else:
                amount = int(amount)
            bank_res = await self.update_bank(interaction.user, -amount)
            wallet_res = await self.update_wallet(interaction.user, +amount)
            if bank_res == 0 or wallet_res == 0:
                return await interaction.response.send_message(
                    "No account found so one was created for you. Please run the command again!")
            wallet, bank, maxbank = await self.get_balance(interaction.user)
            e = discord.Embed(title=f"{amount} coins have been withdrew")
            e.add_field(name="New Wallet", value=wallet)
            e.add_field(name="New Bank", value=f"{bank}/{maxbank}")
            e.set_thumbnail(url=interaction.user.avatar)
            await interaction.response.send_message(embed=e)

        @fresh.command(name="deposit")
        @commands.cooldown(1, 5, commands.BucketType.user)
        async def deposit(interaction: discord.Interaction, amount: int):
            """Deposit coins to your bank."""
            wallet, bank, maxbank = await self.get_balance(interaction.user)
            try:
                amount = int(amount)
            except ValueError:
                pass
            if type(amount) == str:
                if amount.lower() == "max" or amount.lower() == "all":
                    amount = int(maxbank)
            else:
                amount = int(amount)
            bank_res = await self.update_bank(interaction.user, +amount)
            wallet_res = await self.update_wallet(interaction.user, -amount)
            if bank_res == 0 or wallet_res == 0:
                return await interaction.response.send_message(
                    "No account found so one was created for you. Please run the command again!")
            elif bank_res == 1:
                return await interaction.response.send_message(
                    "You don't have enough storage in your bank!")
            wallet, bank, maxbank = await self.get_balance(interaction.user)
            e = discord.Embed(title=f"{amount} coins have been deposited")
            e.add_field(name="New Wallet", value=wallet)
            e.add_field(name="New Bank", value=f"{bank}/{maxbank}")
            e.set_thumbnail(url=interaction.user.avatar)
            await interaction.response.send_message(embed=e)

        @fresh.command(name="give")
        @commands.cooldown(1, 10, commands.BucketType.user)
        async def give(interaction: discord.Interaction, member: discord.Member, amount: int):
            """Give a user some coins."""
            wallet, bank, maxbank = await self.get_balance(interaction.user)
            try:
                amount = int(amount)
            except ValueError:
                pass
            if type(amount) == str:
                if amount.lower() == "max" or amount.lower() == "all":
                    amount = int(wallet)
            else:
                amount = int(amount)
            wallet_res = await self.update_wallet(interaction.user, -amount)
            wallet_res2 = await self.update_wallet(member, +amount)
            if wallet_res == 0 or wallet_res2 == 0:
                return await interaction.response.send_message(
                    f"Either you or {member.mention} didn't have an account so one was created. Please try again.")
            wallet2, bank2, maxbank2 = await self.get_balance(member)
            wallet, bank, maxbank = await self.get_balance(interaction.user)
            e = discord.Embed(title=f"Gave {amount} coins to {member.name}")
            e.add_field(name=f"{interaction.user.name}'s Wallet", value=wallet)
            e.add_field(name=f"{member.name}'s Wallet", value=wallet2)
            e.set_thumbnail(url=interaction.user.avatar)
            await interaction.response.send_message(embed=e)

        @fresh.command(name="gamble")
        @commands.cooldown(1, 10, commands.BucketType.user)
        async def gamble(interaction: discord.Interaction, amount: int=100):
            """Gamble against the odds."""
            wallet, bank, maxbank = await self.get_balance(interaction.user)
            if wallet < 100:
                return await interaction.response.send_message(
                    "You need to have at least 100 coins in your wallet!")
            if amount > 5000:
                return await interaction.response.send_message(
                    "You can't bet more than 5000 coins!")
            if amount > wallet:
                return await interaction.response.send_message(
                    "You don't have enough coins in your wallet!")
            user_strikes = random.randint(1, 20)
            bot_strikes = random.randint(5, 20)
            e = discord.Embed()
            if user_strikes > bot_strikes:
                percentage = random.randint(50, 100)
                amount_won = int(amount * (percentage / 100))
                await self.update_wallet(interaction.user, +amount_won)
                e.description = f"You won **{amount_won}** coins!\nPercentage: {percentage}\nNew Balance: `{wallet + amount_won}`"
                e.set_author(name=interaction.user.name, icon_url=interaction.user.avatar)
                e.color = discord.Color.green()
            elif bot_strikes > user_strikes:
                await self.update_wallet(interaction.user, -amount)
                e.description = f"You lost **{amount}** coins!\nNew Balance: `{wallet - amount}`"
                e.set_author(name=interaction.user.name, icon_url=interaction.user.avatar)
                e.color = discord.Color.red()
            else:
                e.description = f"It was a tie!"
                e.set_author(name=f"Shit Play {interaction.user.name}!", icon_url=interaction.user.avatar)
            e.add_field(name=f"{interaction.user.name.title()}", value=f"Strikes {user_strikes}")
            e.add_field(name=f"{self.bot.user.name}", value=f"Strikes {bot_strikes}")
            e.set_thumbnail(url=interaction.user.avatar)
            return await interaction.response.send_message(embed=e)

        @fresh.command(name="slots")
        @commands.cooldown(1, 10, commands.BucketType.user)
        async def slots(interaction: discord.Interaction, amount: int=100):
            """Play the slot machine."""
            wallet, bank, maxbank = await self.get_balance(interaction.user)
            if wallet < 100:
                return await interaction.response.send_message(
                    "You need to have at least 100 coins in your wallet!")
            if amount > 5000:
                return await interaction.response.send_message(
                    "You can't bet more than 5000 coins!")
            if amount > wallet:
                return await interaction.response.send_message(
                    "You don't have enough coins in your wallet!")
            times_factors = random.randint(1, 5)
            earnings = int(amount * times_factors)
            final = []
            for i in range(3):
                a = random.choice(["🍉", "💎", "💰"])
                final.append(a)
            if final[0] == final[1] or final[0] == final[2] or final[2] == final[0]:
                await self.update_wallet(interaction.user, +earnings)
                e = discord.Embed(color=discord.Color.green())
                e.title = f"You won {earnings} coins!\n"
                e.add_field(name="Outcome:", value=f"{final[0]}{final[1]}{final[2]}", inline=False)
                e.add_field(name="Multiplier:", value=f"X{times_factors}")
                e.add_field(name="New Balance:", value=f"{wallet+earnings}")
                e.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/1055/1055823.png")
                return await interaction.response.send_message(embed=e)
            else:
                await self.update_wallet(interaction.user, -amount)
                e = discord.Embed(color=discord.Color.red())
                e.title = f"You lost {amount} coins!\n\n"
                e.add_field(name="Outcome:", value=f"{final[0]}{final[1]}{final[2]}")
                e.set_thumbnail(url="https://cdn-icons-png.flaticon.com/512/1055/1055823.png")
                return await interaction.response.send_message(embed=e)

        @fresh.command(name="dice")
        @commands.cooldown(1, 10, commands.BucketType.user)
        async def dice(interaction: discord.Interaction, amount: int=100):
            """Roll the dice."""
            pd1 = random.randint(1, 6)
            pd2 = random.randint(1, 6)
            bd1 = random.randint(1, 6)
            bd2 = random.randint(1, 6)
            wallet, bank, maxbank = await self.get_balance(interaction.user)
            if wallet < 100:
                return await interaction.response.send_message(
                    "You need to have at least 100 coins in your wallet!")
            if amount > 5000:
                return await interaction.response.send_message(
                    "You can't bet more than 5000 coins!")
            if amount > wallet:
                return await interaction.response.send_message(
                    "You don't have enough coins in your wallet!")
            # Roll the dice
            await interaction.response.send_message("🎲 Rolling your dice...")
            await asyncio.sleep(1.5)
            await interaction.channel.send(
                content=f"🎲 You rolled a **{pd1}** and a **{pd2}**")
            await asyncio.sleep(1.5)
            await interaction.channel.send(
                content="🎲 Rolling the bots dice...")
            await asyncio.sleep(1.5)
            await interaction.channel.send(
                content=f"🎲 The bot rolled a **{bd1}** and a **{bd2}**")
            await asyncio.sleep(1.5)
            if (pd1 + pd2) > (bd1 + bd2):
                await self.update_wallet(interaction.user, +amount)
                return await interaction.channel.send(
                    content=f"🎲 {interaction.user.mention} You won {amount} coins! Your new balance is {wallet+amount}.")
            elif (pd1 + pd2) < (bd1 + bd2):
                await self.update_wallet(interaction.user, -amount)
                return await interaction.channel.send(
                    content=f"🎲 {interaction.user.mention} You lost {amount} coins! Your new balance is {wallet-amount}.")

    async def create_bank(self, user):
        data = self.db.find_one({"_id": user.id})
        if data is None:
            bankData = {"wallet": 0, "bank": 100, "maxbank": 500, "_id": user.id}
            self.db.insert_one(bankData)
        return

    async def get_balance(self, user):
        data = self.db.find_one({"_id": user.id})
        if data is None:
            await self.create_bank(user)
            return 0, 100, 500
        return data['wallet'], data['bank'], data['maxbank']

    async def update_wallet(self, user, amount: int):
        wallet, bank, maxbank = await self.get_balance(user)
        if wallet is None:
            await self.create_bank(user)
            return 0
        await self.lvl_maxbank(user)
        return self.db.update_one({"_id": user.id}, {"$set": {"wallet": wallet + amount}})

    async def update_bank(self, user, amount: int):
        wallet, bank, maxbank = await self.get_balance(user)
        if bank is None:
            await self.create_bank(user)
            return 0
        if amount > int(maxbank - bank):
            await self.update_wallet(user, amount)
            return 1
        await self.lvl_maxbank(user)
        return self.db.update_one({"_id": user.id}, {"$set": {"bank": bank + amount}})

    async def lvl_maxbank(self, user):
        wallet, bank, maxbank = await self.get_balance(user)
        if maxbank is None:
            await self.create_bank(user)
            return 0
        chance = random.randint(1, 50)
        if 10 < chance and 20 < chance:
            amount = random.randint(1, 100)
            return self.db.update_one({"_id": user.id}, {"$set": {"maxbank": maxbank + amount}})

    async def update_maxbank(self, user, amount: int):
        wallet, bank, maxbank = await self.get_balance(user)
        if maxbank is None:
            await self.create_bank(user)
            return 0
        return self.db.update_one({"_id": user.id}, {"$set": {"maxbank": maxbank + amount}})

async def setup(bot):
    await bot.add_cog(Economy(bot))
