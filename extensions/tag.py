import discord
from discord.ext import commands
from discord import app_commands as Aoi


class Tags(commands.Cog):
    def __init__(self, bot: commands.AutoShardedBot):
        self.bot = bot
        self.db = self.bot.db.tags

    @Aoi.command(name="tag")
    @Aoi.describe(
        tag_name="The tag you would like to get.",
    )
    async def tag(self, interaction: discord.Interaction, tag_name: str):
        """Get a tag."""
        data = await self.db.find_one({"_id": interaction.guild.id})
        print(data)
        if data is None:
            return await interaction.response.send_message(
                "This guild has no tags.",
                ephemeral=True
            )
        for tag in data["tags"]:
            if tag["name"] == tag_name:
                return await interaction.response.send_message(
                    tag["content"]
                )
        await interaction.response.send_message(
            "This tag does not exist.",
            ephemeral=True
        )

    @Aoi.command(name="tag-create", description="Create a tag.")
    async def tag_create(self, interaction: discord.Interaction, name: str, content: str):
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            data = {"_id": interaction.guild.id, "tags": []}
            await self.db.insert_one(data)

        if name in [tag["name"] for tag in data["tags"]]:
            return await interaction.response.send_message(
                "A tag with that name already exists.",
                ephemeral=True
            )

        data["tags"].append(
            {"name": name, "content": content, "author": interaction.user.id})
        await self.db.update_one({"_id": interaction.guild.id}, {"$set": {"tags": data["tags"]}})
        await interaction.response.send_message("Created tag!", ephemeral=True)

    @Aoi.command(name="tag-delete", description="Delete a tag.")
    async def tag_delete(self, interaction: discord.Interaction, name: str):
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            return await interaction.response.send_message(
                "No tags have been created for this guild.",
                ephemeral=True
            )

        if name not in [tag["name"] for tag in data["tags"]]:
            return await interaction.response.send_message(
                "That tag does not exist.",
                ephemeral=True
            )

        tag = [tag for tag in data["tags"] if tag["name"] == name][0]
        permissions = interaction.channel.permissions_for(interaction.user)
        if not permissions.manage_guild and interaction.user.id != tag["author"]:
            return await interaction.response.send_message(
                "You do not have permission to delete this tag.",
                ephemeral=True
            )

        data["tags"] = [tag for tag in data["tags"] if tag["name"] != name]
        await self.db.update_one({"_id": interaction.guild.id}, {"$set": {"tags": data["tags"]}})
        await interaction.response.send_message("Deleted tag!", ephemeral=True)

    @Aoi.command(name="tag-list", description="List all tags.")
    @Aoi.describe(user="The users tags you want.")
    async def tag_list(self, interaction: discord.Interaction, user: discord.User = None):
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            return await interaction.response.send_message(
                "No tags have been created for this guild.",
                ephemeral=True
            )

        if user is not None and user.bot:
            return await interaction.response.send_message(
                "Bots cannot have tags.",
                ephemeral=True
            )

        e = discord.Embed(title="Tags", color=discord.Color.teal())

        if user is None:
            e.title = "All Tags"
            e.description = "\n".join([tag["name"] for tag in data["tags"]])
            e.set_thumbnail(url=interaction.guild.icon)
            if e.description == "":
                e.description = "No tags have been created."
        else:
            e.title = f"{user.name}'s Tags"
            e.description = "\n".join(
                [tag["name"] for tag in data["tags"] if tag["author"] == user.id])
            e.set_thumbnail(url=user.avatar.url)
            if e.description == "":
                e.description = "This user has no tags."

        await interaction.response.send_message(embed=e)

    @Aoi.command(name="tag-edit", description="Edit a tag.")
    async def tag_edit(self, interaction: discord.Interaction, name: str, content: str):
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            return await interaction.response.send_message(
                "No tags have been created for this guild.",
                ephemeral=True
            )

        if name not in [tag["name"] for tag in data["tags"]]:
            return await interaction.response.send_message(
                "That tag does not exist.",
                ephemeral=True
            )

        tag = [tag for tag in data["tags"] if tag["name"] == name][0]
        permissions = interaction.channel.permissions_for(interaction.user)
        if not permissions.manage_guild and interaction.user.id != tag["author"]:
            return await interaction.response.send_message(
                "You do not have permission to edit this tag.",
                ephemeral=True
            )

        tag["content"] = content
        data["tags"] = [tag for tag in data["tags"] if tag["name"] != name]
        data["tags"].append(tag)
        await self.db.update_one({"_id": interaction.guild.id}, {"$set": {"tags": data["tags"]}})
        await interaction.response.send_message("Edited tag!", ephemeral=True)

    @Aoi.command(name="tag-info", description="Get info about a tag.")
    async def tag_info(self, interaction: discord.Interaction, name: str):
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            return await interaction.response.send_message(
                "No tags have been created for this guild.",
                ephemeral=True
            )

        if name not in [tag["name"] for tag in data["tags"]]:
            return await interaction.response.send_message(
                "That tag does not exist.",
                ephemeral=True
            )

        tag = [tag for tag in data["tags"] if tag["name"] == name][0]
        e = discord.Embed(
            title=f"Tag Info: {tag['name']}",
            description=tag["content"],
            color=discord.Color.teal()
        )
        e.set_footer(
            text=f"Created by {interaction.guild.get_member(tag['author'])}")
        await interaction.response.send_message(embed=e)

    @Aoi.command(name="tag-search", description="Search for a tag.")
    async def tag_search(self, interaction: discord.Interaction, *, query: str):
        data = await self.db.find_one({"_id": interaction.guild.id})
        if data is None:
            return await interaction.response.send_message(
                "No tags have been created for this guild.",
                ephemeral=True
            )

        tags = [tag for tag in data["tags"] if query in tag["name"]]
        if not tags:
            return await interaction.response.send_message(
                "No tags were found with that query.",
                ephemeral=True
            )

        e = discord.Embed(
            title=f"Tags matching {query}",
            description="\n".join([tag["name"] for tag in tags]),
            color=discord.Color.teal()
        )
        await interaction.response.send_message(embed=e)

    @tag.error
    @tag_create.error
    @tag_delete.error
    @tag_list.error
    @tag_edit.error
    @tag_info.error
    @tag_search.error
    async def tag_error(self, interaction: discord.Interaction, error: Exception):
        self.bot.logger.error(f"[Tag] Error: {error}")
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
    await bot.add_cog(Tags(bot))
