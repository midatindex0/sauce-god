from datetime import datetime

import discord
from discord.ext import commands, tasks

from bot import BaseBot
from core.utils import read_config

config = read_config()


class Midnight(commands.Cog):
    def __init__(self, bot: BaseBot):
        self.bot = bot
        self.timer = None
        self.online = 0
        self.tracked_timers_day = []
        self.tracked_timers_total = []
        self.midnight_clear_24_track_record.start()

    @tasks.loop(seconds=60)
    async def midnight_track(self):
        vault = self.bot.get_guild(983948184030162964)
        midnight = await vault.fetch_member(823588482273902672)
        if midnight.status != "offline":
            time_enlapsed = (datetime.now() - self.timer).total_seconds()
            if (time_enlapsed / 60) >= 30:
                await self.notify_midnight(time_enlapsed)

    @tasks.loop(seconds=24 * 60 * 24)
    async def midnight_clear_24_track_record(self):
        self.tracked_timers_day.clear()

    @commands.Cog.listener()
    async def on_presence_update(self, b: discord.Member, a: discord.Member):
        if a.id == 823588482273902672:
            b_s, a_s = b.status, a.status
            if b_s == a_s:
                return
            elif b_s != "offline" and a_s != "offline":
                return
            else:
                if b_s == "offline":
                    self.timer = datetime.now()
                    self.midnight_track.start()
                if a_s == "offline":
                    self.midnight_track.stop()
                    enlapsed = (datetime.now() - self.timer).total_seconds()
                    self.timer = None
                    self.tracked_timers_day.append(enlapsed)
                    self.tracked_timers_total.append(enlapsed)

    @commands.Cog.listener()
    async def on_midnight_check(self):
        vault = self.bot.get_guild(983948184030162964)
        midnight = await vault.fetch_member(823588482273902672)
        if midnight.status != "offline":
            self.timer = datetime.now()
            self.midnight_track.start()

    async def notify_midnight(self, enlapsed):
        vault = self.bot.get_guild(983948184030162964)
        midnight = vault.get_member(823588482273902672)
        ch = vault.get_channel(983948184478974052)
        minutes_enlapsed = int(enlapsed / 60)
        await ch.send(
            f"{midnight.mention} You are online for {minutes_enlapsed} minutes. Go study.\n"
        )

    @commands.command(description="Get stats about Midnight", invoke_without_command=True)
    async def midnight(self, ctx: commands.Context):
        await ctx.send(
            f"Midnight was online for **{int(sum(self.tracked_timers_day)/60)} minutes** today.\nTotal online activity tracked: **{int(sum(self.tracked_timers_total)/60)} minutes**.\n_Note: Records are temporary and lost on bot restart_"
        )


async def setup(bot):
    await bot.add_cog(Midnight(bot))
