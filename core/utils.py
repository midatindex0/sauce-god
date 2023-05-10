import aiohttp
import aiosqlite
import tomli
from pytimeparse import parse


def read_config():
    f = open("config.toml", "rb")
    return tomli.load(f)


def _parse(time: str) -> int:
    return int(parse(time))


async def connect() -> aiosqlite.Connection:
    return await aiosqlite.connect("database/bot.db")


async def create_tables():
    db = await connect()
    await db.execute(
        """
        CREATE TABLE IF NOT EXISTS subs(
        member_id INTEGER,
        anime_id INTEGER,
        release INTEGERL,
        dreamh_uri TEXT
    ) 
    """
    )

    await db.commit()
    await db.close()
    return True


async def get_sub_data(search: str) -> dict:
    url = "https://graphql.anilist.co"
    query = """
        query ($id: Int, $page: Int, $perPage: Int, $search: String) {
            Page(page: $page, perPage: $perPage) {
                pageInfo {
                total
                currentPage
                lastPage
                hasNextPage
                perPage
                }
                media(id: $id, search: $search) {
                id
                title {
                    romaji
                }
                nextAiringEpisode {
                    airingAt
                }
                }
            }
        }
    """
    variables = {"search": search}
    async with aiohttp.ClientSession() as session:
        async with session.post(
            url, json={"query": query, "variables": variables}
        ) as resp:
            return (await resp.json())["data"]["Page"]["media"][0]
