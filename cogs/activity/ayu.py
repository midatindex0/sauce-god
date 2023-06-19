from datetime import datetime

import discord
from discord.ext import commands, tasks

from bot import BaseBot
from core.utils import read_config

config = read_config()


class Ayu(commands.Cog):
    def __init__(self, bot: BaseBot):
        self.bot = bot
        self.timer = None
        self.online = 0
        self.tracked_timers_day = []
        self.tracked_timers_total = []
        self.ayu_clear_24_track_record.start()

    @tasks.loop(seconds=60)
    async def ayu_track(self):
        vault = self.bot.get_guild(983948184030162964)
        ayu = await vault.fetch_member(748053138354864229)
        if str(ayu.status) != "offline":
            time_enlapsed = (datetime.now() - self.timer).total_seconds()
            if (time_enlapsed / 60) >= 30:
                await self.notify_ayu(time_enlapsed)

    @tasks.loop(seconds=24 * 60 * 24)
    async def ayu_clear_24_track_record(self):
        self.tracked_timers_day.clear()

    @commands.Cog.listener()
    async def on_presence_update(self, b: discord.Member, a: discord.Member):
        if a.id == 748053138354864229:
            b_s, a_s = str(b.status), str(a.status)
            if b_s == a_s:
                return
            elif b_s != "offline" and a_s != "offline":
                return
            else:
                if b_s == "offline":
                    self.timer = datetime.now()
                    self.ayu_track.start()
                if a_s == "offline":
                    self.ayu_track.stop()
                    enlapsed = (datetime.now() - self.timer).total_seconds()
                    self.timer = None
                    self.tracked_timers_day.append(enlapsed)
                    self.tracked_timers_total.append(enlapsed)

    @commands.Cog.listener()
    async def on_ayu_check(self):
        vault = self.bot.get_guild(983948184030162964)
        ayu = await vault.fetch_member(748053138354864229)
        if str(ayu.status) != "offline":
            self.timer = datetime.now()
            self.ayu_track.start()

    async def notify_ayu(self, enlapsed):
        vault = self.bot.get_guild(983948184030162964)
        ayu = vault.get_member(748053138354864229)
        ch = vault.get_channel(983948184478974052)
        minutes_enlapsed = int(enlapsed / 60)
        await ch.send(
            f"{ayu.mention} You are online for {minutes_enlapsed} minutes. Go study.\n"
        )

    @commands.command(description="Get stats about Ayu", invoke_without_command=True)
    async def ayu(self, ctx: commands.Context):
        await ctx.send(
            f"ayu was online for **{int(sum(self.tracked_timers_day)/60)} minutes** today.\nTotal online activity tracked: **{int(sum(self.tracked_timers_total)/60)} minutes**.\n_Note: Records are temporary and lost on bot restart_"
        )


async def setup(bot):
    await bot.add_cog(Ayu(bot))
