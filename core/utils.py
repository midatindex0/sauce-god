import aiohttp
import aiosqlite
import tomli
from pytimeparse import parse


def read_config():
    f = open("config.toml", "rb")
    return tomli.load(f)

def _parse(time: str) -> int:
    return int(parse(time))