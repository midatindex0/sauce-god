import discord
from discord import Embed, app_commands
from discord.ext import commands
from discord.ui import Button, View, button

from bot import BaseBot
from core.utils import read_config

config = read_config()


class COCInorganic(commands.Cog):
    def __init__(self, bot: BaseBot):
        self.bot = bot

    @app_commands.command(description="Start a game of Inorganic COC")
    async def start(self, interaction: discord.Interaction):
        await interaction.response.defer()
        start_view = GameStartView(interaction.user)
        await interaction.followup.send(view=start_view)


class GameStartView(View):
    def __init__(self, author: discord.Member):
        super().__init__()
        self.author = author

    @button(label="Join", style=discord.ButtonStyle.green)
    async def join(self, interaction: discord.Interaction, button: Button):
        await interaction.response.send_message(
            embed=(Embed(description="work in progress")), ephemeral=True
        )


async def setup(bot):
    await bot.add_cog(COCInorganic(bot))
