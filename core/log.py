import discord
from discord.ext import commands

from bot import BaseBot
from core import error
from core.utils import read_config

config = read_config()


class Log(commands.Cog):
    def __init__(self, bot: BaseBot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_command_error(self, ctx, err):
        err = getattr(err, "original", err)
        err = error.BotException(err, self.bot)
        return await err.propagate()

    @commands.Cog.listener()
    async def on_message_edit(
        self, message_before: discord.Message, message_after: discord.Message
    ):
        if (
            not message_after.author.bot
            and message_before.guild.id == config["default"]["guild_id"]
        ):
            message_log_channel_id = self.bot.config["server"]["message_log_channel"]
            message_log_channel = await self.bot.fetch_channel(message_log_channel_id)
            e = discord.Embed(
                title="Message Edit",
                color=0xF6F600,
                description=f"**Original**: {message_before.content}\n**New**: {message_after.content}",
            )
            e.set_author(
                name=message_after.author.name,
                icon_url=message_after.author.display_avatar,
            )
            await message_log_channel.send(embed=e)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message):
        if (
            not message.author.bot 
            and message.guild.id == config["default"]["guild_id"]
        ):
            message_log_channel_id = self.bot.config["server"]["message_log_channel"]
            message_log_channel = await self.bot.fetch_channel(message_log_channel_id)
            e = discord.Embed(
                title="Message delete",
                color=0xF64800,
                description=f"{message.content}",
            )
            e.set_author(
                name=message.author.name, icon_url=message.author.display_avatar
            )
            await message_log_channel.send(embed=e)


async def setup(bot):
    await bot.add_cog(Log(bot))
