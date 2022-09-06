import json
import aiohttp
import discord
import numpy as np
from discord.ext import commands
from matplotlib import pyplot as plt
from discord import app_commands as Fresh
from playwright.async_api import async_playwright

class Valorant(commands.GroupCog, name="valorant", description="All valorant related commands."):
    def __init__(self, bot):
        self.bot = bot
        self.db = self.bot.db.valorant

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
        except:
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

    @Fresh.command(name="lookup")
    async def val_lookup(self, interaction: discord.Interaction, username: str, tag: str):
        """Lookup a username and tag."""
        await interaction.response.defer()
        account = await self.cred_validate(username, tag)
        if account['status'] != 200:
            return await interaction.followup.send(
                "<:tickNo:697759586538749982> No account found with that username and tag.")
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
            for browser_type in [p.firefox]: 
                browser = await browser_type.launch() 
                page = await browser.new_page()
                await page.goto(f"https://api.tracker.gg/api/v2/valorant/standard/profile/riot/{username}%23{tag}")
                data = json.loads(await page.inner_text('pre'))
                try:
                    if data['errors'][0]['message']=='This profile is still private.':
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
        plt.clf()
        fig, ax = plt.subplots(figsize =(12,5),dpi=200)
        colors = ["#fe7478" if i < 0 else "#41d391" for i in ratings]
        ax.bar(np.arange(0,len(ratings)/2,0.5),ratings, color=colors,zorder=2,width=0.35)
        for s in ['top', 'bottom', 'right']:
            ax.spines[s].set_visible(False)
        ax.spines['left'].set_color('white')
        plt.axhline(y=0, color='white', linestyle='-')
        ax.tick_params(colors='white')
        ax.axes.xaxis.set_visible(False)
        plt.yticks(range(min(ratings)-5, max(ratings) + 7,5))
        ax.grid(b = True, color ='white',
                linestyle ='-', linewidth = 0.5,
                alpha = 0.2,zorder=0)
        for i in ax.patches:
            #print(i)
            if i.get_height()>0:
                plt.text(i.get_x()+0.1, i.get_height()+1, '+' + str(round(i.get_height())),
                    fontsize = 15, fontweight ='bold',
                    color ='white')
            else:
                plt.text(i.get_x()+0.11, i.get_height()-3, str(round(i.get_height())),
                    fontsize = 15, fontweight ='bold',
                    color ='white')
        plt.savefig('ratings.png',transparent=True)
        plt.close()

async def setup(bot):
    await bot.add_cog(Valorant(bot))