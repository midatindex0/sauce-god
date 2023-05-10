from discord.ext import commands
import core.utils as utils

from discord import Embed, Color
config = utils.read_config()

class Subscribe(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
    
    @commands.command(name='connect-db')
    @commands.has_role(config["perms"]["bot_admin_ops_role"])
    async def connection(self, ctx: commands.Context):
        await utils.create_tables()
        self.db = await utils.connect()
        await ctx.reply("Connected to database")
    
    @commands.command(name='subscribe', aliases=['sub'])
    async def subscribe(self, ctx: commands.Context):
        if ctx.message.reference:
            msg = await ctx.fetch_message(ctx.message.reference.message_id)
            if msg.author.id == self.bot.user.id:
                anime = msg.content.split("/")[4]
                try:
                    data = await utils.get_sub_data(anime)
                    self.db = await utils.connect()
                    if data['nextAiringEpisode'] is None:
                        return await ctx.reply(embed=Embed(description=":x: Anime is not airing right now!", color=Color.red()))
                    res = await self.db.execute("SELECT * FROM subs WHERE member_id=? AND anime_id=?",(ctx.author.id, data['id']))
                    res = await res.fetchone()
                    if res:
                        embed = Embed(
                            description=":x: You are already subbed to that anime!",
                            color = Color.gold()
                        )
                        await ctx.reply(embed=embed)
                        return
                    await self.db.execute("INSERT INTO subs VALUES(?,?,?,?)",(ctx.author.id, data['id'], data['nextAiringEpisode']['airingAt'], msg.content))
                    await self.db.commit()
                    await self.db.close()
                    embed = Embed(
                        description=data['title'],
                        color=Color.green()
                    ).add_field(
                        name="Next Episode at:",
                        value=f"<t:{data['nextAiringEpisode']['airingAt']}:F> <t:{data['nextAiringEpisode']['airingAt']}:R>"
                    )
                    await ctx.reply("✅ Subbed:",embed=embed)

                except Exception as e:
                    await ctx.reply(f"Can't find anime: {anime}")
                    channel = self.bot.get_channel(config["server"]["error_log_channel"])
                    await channel.send(f"Error: ```{e}```")
                    raise e
                return

        await ctx.reply("Please reply to a message from me")


async def setup(bot: commands.Bot):
    await bot.add_cog(Subscribe(bot))