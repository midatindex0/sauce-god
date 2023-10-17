# -------------- imports ---------------#

from dotenv import load_dotenv

# Load envirenment variables from .env
load_dotenv()

import logging
import os
from datetime import datetime

import aiohttp
import discord
import tomli
from discord.ext import commands

from core.db.nosql import Driver


# Custom class for the bot, contains configs for logging, databases and stuff
class BaseBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        with open("config.toml", "rb") as f:
            config = tomli.load(f)
            self.config = config
            super().__init__(
                intents=discord.Intents.all(),
                command_prefix=config["default"]["prefix"],
                **kwargs,
            )
            log_handler = logging.FileHandler(
                filename=config["default"]["log_file_prefix"]
                + datetime.now().strftime("%Y-%m-%d %H-%M-%S")
                + ".log",
                encoding="utf-8",
                mode="w",
            )
            stdout_handler = logging.StreamHandler()
            self.logger = logging.getLogger("bot.core")
            formatter = logging.Formatter(
                "%(asctime)s %(levelname)s     %(name)s %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            log_handler.setFormatter(formatter)
            stdout_handler.setFormatter(formatter)
            self.logger.addHandler(log_handler)
            self.logger.addHandler(stdout_handler)
            self.logger.setLevel(logging.DEBUG)

    async def on_ready(self):
        self.session = aiohttp.ClientSession(loop=self.loop)
        self.db = Driver()
        await self.db.connect()
        self.log("Connected to database")
        for extension in self.config["default"]["core_cogs"]:
            await self.load_extension(f"core.{extension}")
        for extension in self.config["cogs"]["custom"]:
            await self.load_extension(f"cogs.custom.{extension}")
        for extension in self.config["cogs"]["list"]:
            await self.load_extension(f"cogs.{extension}")
        await self.tree.sync()
        for event in self.config["events"]["custom_dispatch_on_ready"]:
            self.dispatch(event)
        self.log(
            f"Connected to discord with username: {self.user.display_name}#{self.user.discriminator}"
        )
    
    async def on_member_join(self, member: discord.Member):
        blacklist = [872642439159087106, 744478249719169074]
        if member.id in blacklist:
            await member.ban(reason = "You are not worthy.")

    def run(self):
        TOKEN = os.getenv("TOKEN")
        super().run(TOKEN)

    def log(self, message: str, level=logging.INFO):
        self.logger.log(level, message)
