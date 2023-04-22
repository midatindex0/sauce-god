import discord
import traceback
import logging

class BotException(Exception):
    def __init__(self, err, bot: discord.Client, *args):
        super().__init__(*args)
        self.err = err
        self.bot = bot

    def to_embed(self) -> discord.Embed:
        return discord.Embed(color=0xfc4d25, title=str(self.err), description='\n'.join(traceback.format_exception(self.err)))

    async def propagate(self):
        try:
            error_channel_id = self.bot.config['server']['error_log_channel']
            error_channel = await self.bot.fetch_channel(error_channel_id)
            await error_channel.send(embed=self.to_embed())
        except Exception as e:
            self.bot.log("Could not send error log: {}".format(str(e)), logging.CRITICAL)

def convert(err, bot):
    return BotException(str(err), bot)