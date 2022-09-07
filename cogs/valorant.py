import json
from sqlite3 import Time
import aiohttp
import discord
import numpy
from discord.ext import commands
from matplotlib import pyplot
from discord import app_commands as Fresh
from playwright.async_api import async_playwright

class Valorant(commands.GroupCog, name="valorant", description="All valorant related commands."):
    def __init__(self, bot):
        fresh = bot.tree
        self.bot = bot
        self.db = self.bot.db.valorant

        @fresh.context_menu(name="Valorant Stats")
        async def val_stats_context(interaction: discord.Interaction, member: discord.Member):
            await interaction.response.defer()
            if member is None: member = interaction.user
            account = self.db.find_one({"_id": member.id})
            if account is None:
                return await interaction.followup.send(
                    f"<:tickNo:697759586538749982> No account found for {member.mention}")
            e = discord.Embed(colour=discord.Colour.blurple())
            stats = await self.get_stats(account['data']['name'], account['data']['tag'])
            if stats == "Private":
                return await interaction.followup.send(
                    "<:tickNo:697759586538749982> Account is private, I cannot view stats.")
            e.set_thumbnail(url=stats["avatarUrl"])
            e.set_author(name=stats['user'], icon_url=stats["avatarUrl"])
            e.add_field(name="Win %", value=stats["win_pct"])
            e.add_field(name="Headshot %", value=stats["hs_pct"])
            e.add_field(name="K/D Ratio", value=stats["kd_ratio"])
            rank = await self.get_rank(account['data']['name'], account['data']['tag'], account['data']['region'])
            if rank != "Failed to get comp data.":
                if rank['games_needed_for_rating'] == 0:
                    rankName = f"{rank['currenttierpatched']}, with {rank['ranking_in_tier']}/100 RR."
                    e.add_field(name="Competitive", value=rankName, inline=False)
                    compData = await self.comp_history(
                        account['data']['name'], account['data']['tag'], account['data']['region'])
                    if compData != None:
                        ratings = []
                        try:
                            for match in compData['data']:
                                ratings.append(match['mmr_change_to_last_game'])
                            await self.draw_graph(ratings)
                            image = discord.File("ratings.png",filename="ratings.png")
                            e.set_image(url=f"attachment://ratings.png")
                            e.set_thumbnail(url=account['data']['card']['small'])
                            return await interaction.followup.send(embed=e, file=image)
                        except:
                            return await interaction.followup.send(embed=e)
                    else:
                        return await interaction.followup.send(embed=e)
                else:
                    return await interaction.followup.send(embed=e)
            else:
                return await interaction.followup.send(embed=e)

    @Fresh.command(name="link")
    async def val_link(self, interaction: discord.Interaction, username: str, tag: str):
        """Link your valorant account to your discord."""
        account = self.db.find_one({"_id": interaction.user.id})
        if account is not None:
            return await interaction.response.send_message(
                "<:tickNo:697759586538749982> You already have an account linked!")
        else:
            data = await self.cred_validate(username, tag)
            if data['status'] == 200:
                account = {"_id": interaction.user.id, "data": data['data']}
                self.db.insert_one(account)
                return await interaction.response.send_message(
                    "<:tickYes:697759553626046546> Your account is now linked!")
            else:
                return await interaction.response.send_message(
                    "<:tickNo:697759586538749982> I have failed to fetch your account!")

    @Fresh.command(name="competitive")
    async def val_competitive(self, interaction: discord.Interaction, member: discord.Member=None):
        """Get players competitive RR history."""
        await interaction.response.defer()
        if member is None: member = interaction.user
        account = self.db.find_one({"_id": member.id})
        if account is None:
            return await interaction.followup.send(
                f"<:tickNo:697759586538749982> No account found for {member.mention}")
        data = await self.comp_history(
            account['data']['name'], account['data']['tag'], account['data']['region'])
        if data is None:
            user = f"{account['data']['name']}#{account['data']['tag']}"
            return await interaction.followup.send(
                f"<:tickNo:697759586538749982> No data has been found for {user}")
        try:
            ratings = []
            for match in data['data']:
                ratings.append(match['mmr_change_to_last_game'])
            e = discord.Embed(colour=discord.Colour.blurple())
            e.title = f"{account['data']['name']}'s Match History"
            e.description = f"Current Rank: {data['data'][0]['currenttierpatched']}"
            e.add_field(name="Last game played",value=data['data'][0]['date'])
            await self.draw_graph(ratings)
            image = discord.File("ratings.png",filename="ratings.png")
            e.set_image(url=f"attachment://ratings.png")
            e.set_thumbnail(url=account['data']['card']['small'])
            return await interaction.followup.send(embed=e, file=image)
        except Exception as e:
            print(e)
            return await interaction.followup.send(
                "<:tickNo:697759586538749982> I have failed to fetch your comp data!")

    @Fresh.command(name="stats")
    async def val_stats(self, interaction: discord.Interaction, member: discord.Member=None):
        """Get a players stats."""
        await interaction.response.defer()
        if member is None: member = interaction.user
        account = self.db.find_one({"_id": member.id})
        if account is None:
            return await interaction.followup.send(
                f"<:tickNo:697759586538749982> No account found for {member.mention}")
        e = discord.Embed(colour=discord.Colour.blurple())
        try:
            stats = await self.get_stats(account['data']['name'], account['data']['tag'])
        except TimeoutError:
            return await interaction.followup.send(
                "I was unable to get player stats.")
        if stats == "Private":
            return await interaction.followup.send(
                "<:tickNo:697759586538749982> Account is private, I cannot view stats.")
        e.set_thumbnail(url=stats["avatarUrl"])
        e.set_author(name=stats['user'], icon_url=stats["avatarUrl"])
        e.add_field(name="Win %", value=stats["win_pct"])
        e.add_field(name="Headshot %", value=stats["hs_pct"])
        e.add_field(name="K/D Ratio", value=stats["kd_ratio"])
        rank = await self.get_rank(account['data']['name'], account['data']['tag'], account['data']['region'])
        if rank != "Failed to get comp data.":
            if rank['games_needed_for_rating'] == 0:
                rankName = f"{rank['currenttierpatched']}, with {rank['ranking_in_tier']}/100 RR."
                e.add_field(name="Competitive", value=rankName, inline=False)
                compData = await self.comp_history(
                    account['data']['name'], account['data']['tag'], account['data']['region'])
                if compData != None:
                    ratings = []
                    try:
                        for match in compData['data']:
                            ratings.append(match['mmr_change_to_last_game'])
                        await self.draw_graph(ratings)
                        image = discord.File("ratings.png",filename="ratings.png")
                        e.set_image(url=f"attachment://ratings.png")
                        e.set_thumbnail(url=account['data']['card']['small'])
                        return await interaction.followup.send(embed=e, file=image)
                    except:
                        return await interaction.followup.send(embed=e)
                else:
                    return await interaction.followup.send(embed=e)
            else:
                return await interaction.followup.send(embed=e)
        else:
            return await interaction.followup.send(embed=e)

    @Fresh.command(name="lookup")
    async def val_lookup(self, interaction: discord.Interaction, username: str, tag: str):
        """Lookup a username and tag."""
        await interaction.response.defer()
        account = await self.cred_validate(username, tag)
        if account['status'] != 200:
            return await interaction.followup.send(
                "<:tickNo:697759586538749982> No account found with that username and tag.")
        e = discord.Embed(colour=discord.Colour.blurple())
        try:
            stats = await self.get_stats(account['data']['name'], account['data']['tag'])
        except TimeoutError:
            return await interaction.followup.send(
                "I was unable to get player stats.")
        if stats == "Private":
            return await interaction.followup.send(
                "<:tickNo:697759586538749982> Account is private, I cannot view stats.")
        e.set_thumbnail(url=stats["avatarUrl"])
        e.set_author(name=stats['user'], icon_url=stats["avatarUrl"])
        e.add_field(name="Win %", value=stats["win_pct"])
        e.add_field(name="Headshot %", value=stats["hs_pct"])
        e.add_field(name="K/D Ratio", value=stats["kd_ratio"])
        rank = await self.get_rank(account['data']['name'], account['data']['tag'], account['data']['region'])
        if rank != "Failed to get comp data.":
            if rank['games_needed_for_rating'] == 0:
                rankName = f"{rank['currenttierpatched']}, with {rank['ranking_in_tier']}/100 RR."
                e.add_field(name="Competitive", value=rankName, inline=False)
                compData = await self.comp_history(
                    account['data']['name'], account['data']['tag'], account['data']['region'])
                if compData != None:
                    ratings = []
                    try:
                        for match in compData['data']:
                            ratings.append(match['mmr_change_to_last_game'])
                        await self.draw_graph(ratings)
                        image = discord.File("ratings.png",filename="ratings.png")
                        e.set_image(url=f"attachment://ratings.png")
                        e.set_thumbnail(url=account['data']['card']['small'])
                        return await interaction.followup.send(embed=e, file=image)
                    except:
                        return await interaction.followup.send(embed=e)
                else:
                    return await interaction.followup.send(embed=e)
            else:
                return await interaction.followup.send(embed=e)
        else:
            return await interaction.followup.send(embed=e)

    async def cred_validate(self, username, tag):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.henrikdev.xyz/valorant/v1/account/{username}/{tag}') as r:
                data = await r.json()
                return data

    async def get_rank(self, username, tag, region):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.henrikdev.xyz/valorant/v2/mmr/{region}/{username}/{tag}') as r:
                data = await r.json()
                try:
                    return data["data"]['current_data']
                except KeyError:
                    return "Failed to get comp data."

    async def comp_history(self, username, tag, region):
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://api.henrikdev.xyz/valorant/v1/mmr-history/{region}/{username}/{tag}') as r:
                data=(await r.json()) 
                return data

    async def get_stats(self, username, tag):
        async with async_playwright() as p:
            browser = await p.firefox.launch() 
            page = await browser.new_page()
            await page.goto(f"https://api.tracker.gg/api/v2/valorant/standard/profile/riot/{username}%23{tag}")
            data = json.loads(await page.inner_text('pre'))
            try:
                if data['errors'][0]['message'] == 'This profile is still private.':
                    return "Private"
            except KeyError:
                user = data['data']["platformInfo"]["platformUserHandle"]
                avatarUrl = data['data']["platformInfo"]["avatarUrl"]

                stats = data['data']["segments"][0]["stats"]
                win_pct = stats["matchesWinPct"]["displayValue"]
                hs_pct = stats["headshotsPercentage"]["displayValue"]
                kd_ratio = stats["kDRatio"]["displayValue"]
                aces = stats["aces"]["displayValue"]
                time_played = stats["timePlayed"]["displayValue"]
                try:
                    rank = stats["rank"]["metadata"]["tierName"]
                    rankIconUrl = stats["rank"]["metadata"]["iconUrl"]
                except:
                    rank = "Unrated"
                    rankIconUrl = "https://media.valorant-api.com/competitivetiers/564d8e28-c226-3180-6285-e48a390db8b1/0/smallicon.png"

                DATA = dict(
                    user=user,
                    avatarUrl=avatarUrl,
                    win_pct=win_pct,
                    hs_pct=hs_pct,
                    kd_ratio=kd_ratio,
                    aces=aces,
                    time_played=time_played,
                    rank=rank,
                    rankIconUrl=rankIconUrl,
                )
                return DATA

    async def draw_graph(self, ratings):
        pyplot.clf()
        color = ["#fe7478" if i < 0 else "#41d391" for i in ratings]
        figure, axes = pyplot.subplots(figsize=(10, 2.5), dpi=150)
        axes.tick_params(colors='white')
        axes.axes.xaxis.set_visible(False)
        axes.bar(numpy.arange(0, len(ratings) / 2,0.5), ratings, color=color, zorder=1, width=.4)
        for spine in ['top', 'bottom', 'right', 'left']:
            if spine == 'left':
                axes.spines['left'].set_color('white')
            else:
                axes.spines[spine].set_visible(False)
        pyplot.axhline(color='white', linestyle='-')
        pyplot.yticks(range(min(ratings)-5, max(ratings) + 7,5))
        axes.grid(color='white', alpha=0.1)
        for bar in axes.patches:
            x = bar.get_x()
            height = bar.get_height()
            if height > 0:
                pyplot.text(x + .06, height + 1.5, '+' + str(round(height)),
                    fontsize=10, color='white')
            else:
                pyplot.text(x + .06, height - 3.5, str(round(height)),
                    fontsize=10, color='white')
        pyplot.savefig('ratings.png', transparent=True)
        pyplot.close()

async def setup(bot):
    await bot.add_cog(Valorant(bot))