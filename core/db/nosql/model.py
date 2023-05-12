from typing import List

from beanie import Document, PydanticObjectId


class AnimeSubscribeModel(Document):
    anilist_id: int
    member_ids: List[int]
    anime_slug: str
    anime_title: str
    next_release: int
    episode: int

    async def notify(self, channel):
        pings = "".join(map(lambda id: "<@{}>".format(id), self.member_ids))
        await channel.send(
            f"**{self.anime_title}** episode {self.episode} released!\n[{pings}]\nStream now at https://d2o5.vercel.app/anime/{self.anime_slug}/{self.episode}"
        )


model_list = [AnimeSubscribeModel]
