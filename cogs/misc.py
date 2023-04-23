import discord
from discord import app_commands, Embed
from discord.ext import commands
from discord.ui import View, button, Button
from core import error
from core.utils import read_config
from bot import BaseBot

from time import time

config = read_config()

class Misc(commands.Cog):
    def __init__(self, bot: BaseBot):
        self.bot = bot

    @commands.command(description="Check bot latency")
    async def ping(self, ctx: commands.Context, *, options=None):
        ed = Embed(color=discord.Color.random(), title="Checking bot latency")
        m = await ctx.send(embed=ed)
        pings = []
        desc = ""
        for i in range(4):
            desc += "\npinging...⏳"
            ed.description = desc
            t1 = time()
            await m.edit(embed=ed)
            t2 = time()
            pings.append((t2 - t1) * 1000)
            desc = desc[: desc.rfind("\n")]
            desc += (
                f"\n{i+1}. **{(t2-t1)*1000:.2f}ms** {'🔴' if pings[-1] > 600 else '🟢'}"
            )
            ed.description = desc
            await m.edit(embed=ed)
        avr_ping = sum(pings) / len(pings)
        if avr_ping < 500:
            ed.color = 0x32FC4D
        elif avr_ping < 600:
            ed.color = 0xDAFC32
        else:
            ed.color = 0xFC4A32
        ed.add_field(name="Real Latency ⌛", value=f"{avr_ping:.1f}ms", inline=True)
        ed.add_field(
            name="Ideal Latency 🕐", value=f"{self.bot.latency*1000:.1f}ms", inline=True
        )
        await m.edit(embed=ed)


async def setup(bot):
    await bot.add_cog(Misc(bot))
