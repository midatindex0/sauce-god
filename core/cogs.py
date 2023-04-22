import discord
from discord.ext import commands
from core import error
from core.utils import read_config
from bot import BaseBot

config = read_config()

class CogsOps(commands.Cog):
    def __init__(self, bot: BaseBot):
        self.bot = bot

    @commands.group(description="Cog related commands", invoke_without_command=True)
    @commands.has_role(config['perms']['cog_ops_access_role'])
    async def cog(self, ctx: commands.Context):
        loaded_cogs = []
        unloaded_cogs = []
        for ext in self.bot.config["default"]["core_cogs"]:
            try:
                await self.bot.load_extension(f"core.{ext}")
            except commands.ExtensionAlreadyLoaded:
                loaded_cogs.append(ext)
            except commands.ExtensionNotFound:
                unloaded_cogs.append(ext)
        for ext in self.bot.config["cogs"]["custom"]:
            try:
                await self.bot.load_extension(f"cogs.custom.{ext}")
            except commands.ExtensionAlreadyLoaded:
                loaded_cogs.append(ext)
            except commands.ExtensionNotFound:
                unloaded_cogs.append(ext)
        for ext in self.bot.config["cogs"]["list"]:
            try:
                await self.bot.load_extension(f"cogs.{ext}")
            except commands.ExtensionAlreadyLoaded:
                loaded_cogs.append(ext)
            except commands.ExtensionNotFound:
                unloaded_cogs.append(ext)
        await ctx.send(f"```\nLoaded cogs: {', '.join(loaded_cogs)}\nUnloaded cogs: {','.join(unloaded_cogs)}```")


    @cog.command()
    async def rel(self, ctx: commands.Context, ext):
        self.bot.log(
            f"Cog [{ext}] reload initiated by @{ctx.author.name}#{ctx.author.discriminator} [{ctx.author.id}]"
        )
        if ext in self.bot.config["default"]["core_cogs"]:
            msg = await ctx.send("`Reloading core cog: {}` 🛠️".format(ext))
            try:
                await self.bot.reload_extension("core.{}".format(ext))
                await msg.edit(content="`Reloaded core cog: {}` 🆗".format(ext))
            except Exception as e:
                await msg.edit(content="`Failed to reload core cog: {}` 🔴".format(ext))
                raise e

        else:
            msg = await ctx.send("`Trying to reload cog: {}` 🛠️".format(ext))
            try:
                await self.bot.reload_extension("cogs.{}".format(ext))
                await msg.edit(content="`Reloaded cog: {}` 🆗".format(ext))
            except Exception as e:
                await msg.edit(content="`Failed to reload cog: {}` 🔴".format(ext))
                raise e


async def setup(bot):
    await bot.add_cog(CogsOps(bot))
