from datetime import datetime

import discord
from discord.ext import commands, tasks

from bot import BaseBot
from core.utils import read_config

config = read_config()


class Zapp(commands.Cog):
    def __init__(self, bot: BaseBot):
        self.bot = bot
        self.timer = None
        self.online = 0
        self.tracked_timers_day = []
        self.tracked_timers_total = []
        self.zapp_clear_24_track_record.start()

    @tasks.loop(seconds=60)
    async def zapp_track(self):
        vault = self.bot.get_guild(983948184030162964)
        zapp = await vault.fetch_member(903667860499484742)
        if str(zapp.status) != "offline":
            time_enlapsed = (datetime.now() - self.timer).total_seconds()
            if (time_enlapsed / 60) >= 30:
                await self.notify_zapp(time_enlapsed)

    @tasks.loop(seconds=24 * 60 * 24)
    async def zapp_clear_24_track_record(self):
        self.tracked_timers_day.clear()

    @commands.Cog.listener()
    async def on_presence_update(self, b: discord.Member, a: discord.Member):
        if a.id == 903667860499484742:
            b_s, a_s = str(b.status), str(a.status)
            if b_s == a_s:
                return
            elif b_s != "offline" and a_s != "offline":
                return
            else:
                if b_s == "offline":
                    self.timer = datetime.now()
                    self.zapp_track.start()
                if a_s == "offline":
                    self.zapp_track.stop()
                    enlapsed = (datetime.now() - self.timer).total_seconds()
                    self.timer = None
                    self.tracked_timers_day.append(enlapsed)
                    self.tracked_timers_total.append(enlapsed)

    @commands.Cog.listener()
    async def on_zapp_check(self):
        vault = self.bot.get_guild(983948184030162964)
        zapp = await vault.fetch_member(903667860499484742)
        if str(zapp.status) != "offline":
            self.timer = datetime.now()
            self.zapp_track.start()

    async def notify_zapp(self, enlapsed):
        vault = self.bot.get_guild(983948184030162964)
        zapp = vault.get_member(903667860499484742)
        ch = vault.get_channel(983948184478974052)
        minutes_enlapsed = int(enlapsed / 60)
        await ch.send(
            f"{zapp.mention} You are online for {minutes_enlapsed} minutes. Go study.\n"
        )

    @commands.command(description="Get stats about Zapp", invoke_without_command=True)
    async def zapp(self, ctx: commands.Context):
        await ctx.send(
            f"zapp was online for **{int(sum(self.tracked_timers_day)/60)} minutes** today.\nTotal online activity tracked: **{int(sum(self.tracked_timers_total)/60)} minutes**.\n_Note: Records are temporary and lost on bot restart_"
        )


async def setup(bot):
    await bot.add_cog(Zapp(bot))
