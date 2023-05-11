import aiohttp
from discord import Color, Embed
from discord.ext import commands

from core import utils
from core.db.nosql.model import AnimeSubscribeModel

config = utils.read_config()


class Subscribe(commands.Cog):
    def __init__(self, bot: commands.Bot, session: aiohttp.ClientSession) -> None:
        self.bot = bot
        self.session = session

    async def anilist_get(self, slug: str):
        url = "https://graphql.anilist.co"
        query = """
            query ($id: Int, $search: String) {
                Media(id: $id, search: $search) {
                    id
                    title {
                    romaji
                    }
                    nextAiringEpisode {
                    airingAt
                    episode
                    }
                }
            }
        """
        variables = {"search": slug.replace("-", " ")}
        resp = await self.session.post(
            url, json={"query": query, "variables": variables}
        )
        res = await resp.json()
        if resp.ok:
            return res["data"]["Media"]
        else:
            return None

    @commands.command(name="subscribe", aliases=["sub"])
    @commands.cooldown(1, 5, commands.BucketType.user)  # <--- Tapu proof
    async def subscribe(self, ctx: commands.Context):
        if ctx.message.reference:
            msg = await ctx.fetch_message(ctx.message.reference.message_id)
            if msg.author.id == self.bot.user.id and "/anime/" in msg.content:
                anime = msg.content.split("/")[4]
                data = await self.anilist_get(anime)
                if data["nextAiringEpisode"] is None:
                    return await ctx.reply(
                        embed=Embed(
                            description=":x: Anime is not airing right now!",
                            color=Color.red(),
                        )
                    )
                res = await AnimeSubscribeModel.find_one(
                    AnimeSubscribeModel.anilist_id == data["id"]
                )
                if res:
                    if ctx.author.id in res.member_ids:
                        embed = Embed(
                            description=":x: You are already subbed to that anime!",
                            color=Color.gold(),
                        )
                        await ctx.reply(embed=embed)
                        return
                    else:
                        await res.set(
                            {
                                AnimeSubscribeModel.member_ids: res.member_ids.append(
                                    ctx.author.id
                                )
                            }
                        )
                else:
                    sub_model = AnimeSubscribeModel(
                        member_ids=[ctx.author.id],
                        anilist_id=data["id"],
                        anime_slug=anime,
                        next_release=data["nextAiringEpisode"]["airingAt"],
                        episode=data["nextAiringEpisode"]["episode"],
                    )
                    await sub_model.insert()

                embed = Embed(
                    description=data["title"]["romaji"], color=Color.green()
                ).add_field(
                    name=f"Episode {data['nextAiringEpisode']['episode']} at:",
                    value=f"<t:{data['nextAiringEpisode']['airingAt']}:F> (<t:{data['nextAiringEpisode']['airingAt']}:R>)",
                )
                await ctx.reply("✅ Subbed:", embed=embed)
                return
        await ctx.reply("Please reply to a message from me")


async def setup(bot: commands.Bot):
    session = aiohttp.ClientSession(loop=bot.loop)
    await bot.add_cog(Subscribe(bot, session))
