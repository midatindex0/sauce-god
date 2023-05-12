from discord.ext import commands

from bot import BaseBot
from core.utils import read_config

config = read_config()


class HAnime(commands.Cog):
    def __init__(self, bot: BaseBot):
        self.bot = bot
        self.session = bot.session

    @commands.group(description="Search hanimes and more", invoke_without_command=True)
    @commands.is_nsfw()
    async def hanime(self, ctx: commands.Context, *, name: str):
        pass


async def setup(bot):
    await bot.add_cog(HAnime(bot))
