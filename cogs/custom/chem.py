from discord.ext import commands

from bot import BaseBot
from core.utils import read_config

config = read_config()


class Chem(commands.Cog):
    def __init__(self, bot: BaseBot):
        self.bot = bot


async def setup(bot):
    await bot.add_cog(Chem(bot))
