from time import time

from discord import Color, Embed
from discord.ext import commands, tasks
from pydantic import BaseModel

from core import utils
from core.db.nosql.model import AnimeSubscribeModel

config = utils.read_config()


class AnimeTitleProject(BaseModel):
    anime_title: str
    next_release: int


class Subscribe(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.session = bot.session
        self.anime_publish.start()

    def cog_unload(self):
        self.anime_publish.cancel()

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

    @commands.command(
        name="airing", help="checking airing schedule of an anime", aliases=["air"]
    )
    @commands.cooldown(1, 5, commands.BucketType.user)  # <--- Tapu proof
    async def _air(self, ctx: commands.Context):
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
                embed = Embed(
                    description=data["title"]["romaji"], color=Color.green()
                ).add_field(
                    name=f"Episode {data['nextAiringEpisode']['episode']} at:",
                    value=f"<t:{data['nextAiringEpisode']['airingAt']}:F> (<t:{data['nextAiringEpisode']['airingAt']}:R>)",
                )
                await ctx.reply(embed=embed)
                return
        await ctx.reply("Please reply to anime link from me")

    @commands.command(
        name="subscribe",
        help="Get notified when new episode is released",
        aliases=["sub"],
    )
    @commands.cooldown(1, 5, commands.BucketType.user)  # <--- Tapu proof
    async def subscribe(self, ctx: commands.Context):
        if ctx.message.reference:
            msg = await ctx.fetch_message(ctx.message.reference.message_id)
            if msg.author.id == self.bot.user.id and "/anime/" in msg.content:
                anime = msg.content.split("/")[4]
                data = await self.anilist_get(anime)
                if not data:
                    await ctx.reply("Could not find anime")
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
                            color=Color.red(),
                        )
                        await ctx.reply(embed=embed)
                        return
                    else:
                        res.member_ids.append(ctx.author.id)
                        await res.save()
                else:
                    sub_model = AnimeSubscribeModel(
                        member_ids=[ctx.author.id],
                        anilist_id=data["id"],
                        anime_slug=anime,
                        anime_title=data["title"]["romaji"],
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
        await ctx.reply("Please reply to an anime link from me")

    @commands.command(
        name="unsubscribe",
        help="Unsubscribe from new release notification",
        aliases=["unsub"],
    )
    async def unsubscribe(self, ctx: commands.Context):
        if ctx.message.reference:
            msg = await ctx.fetch_message(ctx.message.reference.message_id)
            if msg.author.id == self.bot.user.id and "/anime/" in msg.content:
                anime = msg.content.split("/")[4]
                res = await AnimeSubscribeModel.find_one(
                    AnimeSubscribeModel.anime_slug == anime
                )
                if res and ctx.author.id in res.member_ids:
                    if len(res.member_ids) != 1:
                        res.member_ids.remove(ctx.author.id)
                        await res.save()
                    else:
                        await res.delete()
                    return await ctx.reply("✅ Unsubscribed")
                return await ctx.reply("You are not subscribed to this anime")
        await ctx.reply("Please reply to an anime link from me")

    @commands.command(name="subscriptions", help="List subscriptions", aliases=["subs"])
    async def subscriptions(self, ctx: commands.Context):
        subs = (
            await AnimeSubscribeModel.find(
                AnimeSubscribeModel.member_ids == ctx.author.id
            )
            .project(AnimeTitleProject)
            .to_list()
        )
        if subs:
            return await ctx.reply(
                embed=Embed(
                    title="Anime Subscriptions",
                    description="\n".join(
                        map(
                            lambda s: s.anime_title + f" - airs <t:{s.next_release}:R>",
                            subs,
                        )
                    ),
                    color=Color.green(),
                ),
            )
        return await ctx.reply(
            embed=Embed(
                description=":x: You are not subscribed to any anime",
                color=Color.red(),
            )
        )

    @tasks.loop(seconds=5 * 60)
    async def anime_publish(self):
        animes = await AnimeSubscribeModel.find_all().to_list()
        for anime in animes:
            if anime.next_release <= int(time()):
                res = await self.session.get(
                    f"https://d2o5.vercel.app/anime/{anime.anime_slug}/episode/{anime.episode}"
                )
                if res.ok:
                    await anime.notify(
                        await self.bot.fetch_channel(
                            config["server"]["notification_channel"]
                        )
                    )
                    data = await self.anilist_get(anime.anime_slug)
                    if data["nextAiringEpisode"]:
                        anime.next_release = data["nextAiringEpisode"]["airingAt"]
                        anime.episode = data["nextAiringEpisode"]["episode"]
                        await anime.save()
                    else:
                        await anime.delete()


async def setup(bot: commands.Bot):
    await bot.add_cog(Subscribe(bot))
