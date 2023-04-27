from time import time

from discord import Color, Embed
from discord.ext import commands

from bot import BaseBot
from core.utils import read_config

config = read_config()


class Misc(commands.Cog):
    def __init__(self, bot: BaseBot):
        self.bot = bot

    @commands.command(name="ping", help="Returns Latency")
    async def ping(self, ctx: commands.Context):
        embed = Embed(description="Calculating Latency...", color=Color.green())
        msg = await ctx.reply(embed=embed)

        def get_color(latency):
            if latency < 100:
                return Color.green()
            elif latency < 150:
                return Color.gold()
            else:
                return Color.red()

        total = 0
        times = 6
        start_time = time()
        async with ctx.typing():
            for i in range(times):
                latency = round(self.bot.latency * 1000, 2)
                embed.add_field(
                    name=f"Latency {i+1}",
                    value=f"{latency}ms",
                )
                embed.color = get_color(latency)
                await msg.edit(embed=embed)
                total += latency

        time_taken = round((time() - start_time) * 1000, 2)
        average = (
            round(total / times, 2),
            round(time_taken / times, 2),
        )
        embed = (
            Embed(description="Pong!", color=get_color(average[0]))
            .add_field(
                name="<a:api_latency:1016016946594058321> Avg. API Latency",
                value=f"{average[0]}ms",
                inline=False,
            )
            .add_field(
                name="<a:typing:1099347116003950642> Avg. Return Time",
                value=f"{average[1]}ms",
                inline=False,
            )
        )  # I'll add backend latency soon, and if we will work with a db then a db latency as well
        await msg.edit(embed=embed)

    @commands.command(name="status", help="Show bot status")
    # wip
    async def status_(self, ctx: commands.Context):
        ...
        # await ctx.reply("wip") NOTE: will work with psutil


async def setup(bot):
    await bot.add_cog(Misc(bot))
