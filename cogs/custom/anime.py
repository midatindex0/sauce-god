import discord
from discord import app_commands, Embed
from discord.ext import commands
from core import error
from core.utils import read_config
from bot import BaseBot

import asyncio
import aiohttp

config = read_config()


class Anime(commands.Cog):
    def __init__(self, bot: BaseBot, session: aiohttp.ClientSession):
        self.bot = bot
        self.session = session

    @commands.group(description="Search anime and more", invoke_without_command=True)
    async def anime(self, ctx: commands.Context, *, name: str):
        res = await self.session.get(
            f'https://d2o5-backend.vercel.app/anime/search?query={name.replace(" ", "+")}'
        )
        if res.ok:
            data = await res.json()
            names = Embed(title="Choose anime")
            desc = ""
            if not data:
                return await ctx.send("No anime found.")
            for i, obj in enumerate(data):
                desc += f"{i+1}: {obj['title']} ({obj['released'].replace(' Released: ', '')})\n\n"
            names.description = desc
            msg = await ctx.send(embed=names)
            try:
                index = await ctx.bot.wait_for(
                    "message",
                    check=lambda m: m.author.id == ctx.author.id
                    and m.content.isdigit(),
                    timeout=60*3,
                )
                selected = data[int(index.content) - 1]
                await ctx.send(f"https://d2o5.vercel.app/anime/{selected['slug']}")
            except asyncio.TimeoutError:
                pass
            except (ValueError, IndexError):
                await ctx.send("Invalid choice")
            finally:
                await msg.delete()
        else:
            await ctx.send("Some error occured while fetching data")
            return


async def setup(bot):
    session = aiohttp.ClientSession(loop=bot.loop)
    await bot.add_cog(Anime(bot, session))
