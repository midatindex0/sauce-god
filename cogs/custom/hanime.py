import aiohttp
from discord.ext import commands

from bot import BaseBot
from core.utils import read_config

config = read_config()


class HAnime(commands.Cog):
    def __init__(self, bot: BaseBot, session: aiohttp.ClientSession):
        self.bot = bot
        self.session = session

    @commands.group(description="Search hanimes and more", invoke_without_command=True)
    @commands.is_nsfw()
    async def hanime(self, ctx: commands.Context, *, name: str):
        pass


async def setup(bot):
    session = aiohttp.ClientSession(loop=bot.loop)
    await bot.add_cog(HAnime(bot, session))
