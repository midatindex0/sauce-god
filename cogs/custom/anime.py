import asyncio

from discord import Embed
from discord.ext import commands

from bot import BaseBot
from core.utils import read_config

config = read_config()


class Anime(commands.Cog):
    def __init__(self, bot: BaseBot):
        self.bot = bot
        self.session = bot.session

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
                    timeout=60 * 3,
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
    await bot.add_cog(Anime(bot))
