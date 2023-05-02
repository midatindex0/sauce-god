from time import time

import psutil
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
    @commands.has_role(config["perms"]["bot_admin_ops_role"])
    async def status_(self, ctx: commands.Context):
        cpu_percent = psutil.cpu_percent()
        mem_percent = psutil.virtual_memory().percent
        round(self.bot.latency * 1000, 2)
        disk_percent = psutil.disk_usage("/").percent
        embed = (
            Embed(description="Bot Status", color=Color.green())
            .add_field(
                name="<:CPU:1016016795909488651> CPU Usage",
                value=f"```{cpu_percent}%```",
                inline=False,
            )
            .add_field(
                name="<:memory:1016016586584363079> Memory Usage",
                value=f"```{mem_percent}%```",
                inline=False,
            )
            .add_field(
                name="<a:disk:1094229488239378573> Disk Usage",
                value=f"```{disk_percent}%```",
                inline=False,
            )
            .add_field(
                name="<a:api_latency:1016016946594058321> API Latency",
                value=f"```128ms```",
                inline=False,
            )
        )
        await ctx.reply(embed=embed)


async def setup(bot):
    await bot.add_cog(Misc(bot))
