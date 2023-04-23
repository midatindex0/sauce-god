from discord.ext import commands

from core import error


class Log(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, err):
        err = getattr(err, "original", err)
        err = error.BotException(err, self.bot)
        return await err.propagate()


async def setup(bot):
    await bot.add_cog(Log(bot))
