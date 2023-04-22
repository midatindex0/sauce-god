import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import View, button, Button
from core import error
from core.utils import read_config
from bot import BaseBot

config = read_config()


class COCInorganic(commands.Cog):
    def __init__(self, bot: BaseBot):
        self.bot = bot

    @app_commands.command(description="Start a game of Inorganic COC")
    async def start(self, interaction: discord.Interaction):
        start_view = GameStartView()
        await ctx.send(view=start_view)


class GameStartView(View):
    def __init__(self, author: discord.Member):
        super().__init__()
        self.author = author

    @button(label="Join", style=discord.ButtonStyle.green)
    async def join(self, button: Button, interaction: discord.Interaction):
        pass


async def setup(bot):
    await bot.add_cog(COCInorganic(bot))
