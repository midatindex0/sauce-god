from typing import List

from beanie import Document


class AnimeSubscribeModel(Document):
    member_ids: List[int]
    anilist_id: int
    anime_slug: str
    next_release: int
    episode: int


model_list = [AnimeSubscribeModel]
