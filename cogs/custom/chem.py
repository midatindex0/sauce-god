import discord
from discord import Embed, app_commands
from discord.ext import commands
from discord.ui import Button, View, button
import io

from bot import BaseBot
from core.utils import read_config

from rdkit import Chem as chem
from rdkit.Chem import Draw as draw

config = read_config()


class Chem(commands.Cog):
    def __init__(self, bot: BaseBot):
        self.bot = bot

async def setup(bot):
    await bot.add_cog(Chem(bot))
