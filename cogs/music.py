import asyncio
import itertools
import sys
import traceback
from functools import partial

import discord
from async_timeout import timeout
from discord import Color, Embed
from discord.ext import commands
from yt_dlp import YoutubeDL

ytdlopts = {
    "format": "bestaudio/best",
    "outtmpl": "downloads/%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "noplaylist": True,
    "nocheckcertificate": True,
    "ignoreerrors": False,
    "logtostderr": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",  # ipv6 addresses cause issues sometimes
}

ffmpegopts = {"before_options": "-nostdin", "options": "-vn"}

ytdl = YoutubeDL(ytdlopts)


class VoiceConnectionError(commands.CommandError):
    """Custom Exception class for connection errors."""


class InvalidVoiceChannel(VoiceConnectionError):
    """Exception for cases of invalid Voice Channels."""


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, requester):
        super().__init__(source)
        self.requester = requester

        self.title = data.get("title")
        self.web_url = data.get("webpage_url")

        # YTDL info dicts (data) have other useful information you might want
        # https://github.com/rg3/youtube-dl/blob/master/README.md

    def __getitem__(self, item: str):
        """Allows us to access attributes similar to a dict.
        This is only useful when you are NOT downloading.
        """
        return self.__getattribute__(item)

    @classmethod
    async def create_source(cls, ctx, search: str, *, loop, download=False):
        loop = loop or asyncio.get_event_loop()

        to_run = partial(ytdl.extract_info, url=search, download=download)
        data = await loop.run_in_executor(None, to_run)

        if "entries" in data:
            # take first item from a playlist
            data = data["entries"][0]

        embed = Embed(
            description=f"```Added {data['title']} to the Queue```",
            color=Color.blurple(),
        ).set_footer(text=f"Requested by {str(ctx.author)}")

        if download:
            source = ytdl.prepare_filename(data)
        else:
            return {
                "webpage_url": data["webpage_url"],
                "requester": ctx.author,
                "title": data["title"],
            }

        return cls(discord.FFmpegPCMAudio(source), data=data, requester=ctx.author)

    @classmethod
    async def regather_stream(cls, data, *, loop):
        """Used for preparing a stream, instead of downloading.
        Since Youtube Streaming links expire."""
        loop = loop or asyncio.get_event_loop()
        requester = data["requester"]

        to_run = partial(ytdl.extract_info, url=data["webpage_url"], download=False)
        data = await loop.run_in_executor(None, to_run)

        return cls(discord.FFmpegPCMAudio(data["url"]), data=data, requester=requester)


class MusicPlayer(commands.Cog):
    """A class which is assigned to each guild using the bot for Music.
    This class implements a queue and loop, which allows for different guilds to listen to different playlists
    simultaneously.
    When the bot disconnects from the Voice it's instance will be destroyed.
    """

    __slots__ = (
        "bot",
        "_guild",
        "_channel",
        "_cog",
        "queue",
        "next",
        "current",
        "np",
        "volume",
    )

    def __init__(self, ctx):
        self.bot = ctx.bot
        self._guild = ctx.guild
        self._channel = ctx.channel
        self._cog = ctx.cog

        self.queue = asyncio.Queue()
        self.next = asyncio.Event()

        self.np = None  # Now playing message
        self.volume = 0.5
        self.current = None

        ctx.bot.loop.create_task(self.player_loop())

    async def player_loop(self):
        """Our main player loop."""
        await self.bot.wait_until_ready()

        while not self.bot.is_closed():
            self.next.clear()

            try:
                # Wait for the next song. If we timeout cancel the player and disconnect...
                async with timeout(300):  # 5 minutes...
                    source = await self.queue.get()
            except asyncio.TimeoutError:
                return self.destroy(self._guild)

            if not isinstance(source, YTDLSource):
                # Source was probably a stream (not downloaded)
                # So we should regather to prevent stream expiration
                try:
                    source = await YTDLSource.regather_stream(
                        source, loop=self.bot.loop
                    )
                except Exception as e:
                    await self._channel.send(
                        f"There was an error processing your song.\n"
                        f"```css\n[{e}]\n```"
                    )
                    continue

            source.volume = self.volume
            self.current = source

            self._guild.voice_client.play(
                source,
                after=lambda _: self.bot.loop.call_soon_threadsafe(self.next.set),
            )
            self.np = await self._channel.send(
                f"**Now Playing:** `{source.title}` requested by "
                f"`{source.requester}`"
            )
            await self.next.wait()

            # Make sure the FFmpeg process is cleaned up.
            source.cleanup()
            self.current = None

            try:
                # We are no longer playing this song...
                await self.np.delete()
            except discord.HTTPException:
                pass

    def destroy(self, guild):
        """Disconnect and cleanup the player."""
        return self.bot.loop.create_task(self._cog.cleanup(guild))


class Music(commands.Cog):
    """Music related commands."""

    __slots__ = ("bot", "players")

    def __init__(self, bot):
        self.bot = bot
        self.players = {}

    async def cleanup(self, guild):
        try:
            await guild.voice_client.disconnect()
        except AttributeError:
            pass

        try:
            del self.players[guild.id]
        except KeyError:
            pass

    async def __local_check(self, ctx):
        """A local check which applies to all commands in this cog."""
        if not ctx.guild:
            raise commands.NoPrivateMessage
        return True

    async def __error(self, ctx, error):
        """A local error handler for all errors arising from commands in this cog."""
        if isinstance(error, commands.NoPrivateMessage):
            try:
                return await ctx.reply(
                    embed=Embed(
                        description="This command can only be used in a server.",
                        color=Color.red(),
                    )
                )
            except discord.HTTPException:
                pass
        elif isinstance(error, InvalidVoiceChannel):
            await ctx.reply(
                embed=Embed(
                    description="Error connecting to Voice Channel.\nPlease make sure you are in a valid channel or provide me with one",
                    color=Color.red(),
                )
            )

        print("Ignoring exception in command {}:".format(ctx.command), file=sys.stderr)
        traceback.print_exception(
            type(error), error, error.__traceback__, file=sys.stderr
        )

    def get_player(self, ctx):
        """Retrieve the guild player, or generate one."""
        try:
            player = self.players[ctx.guild.id]
        except KeyError:
            player = MusicPlayer(ctx)
            self.players[ctx.guild.id] = player

        return player

    @commands.command(name="connect", aliases=["join"])
    async def connect_(self, ctx: commands.Context):
        try:
            channel = ctx.author.voice.channel
        except AttributeError:
            raise InvalidVoiceChannel("No channel to join.")

        vc = ctx.voice_client

        if vc:
            if vc.channel.id == channel.id:
                return
            try:
                await vc.move_to(channel)
            except asyncio.TimeoutError:
                raise VoiceConnectionError(f"Moving to channel: <{channel}> timed out.")
        else:
            try:
                await channel.connect()
            except asyncio.TimeoutError:
                raise VoiceConnectionError(
                    f"Connecting to channel: <{channel}> timed out."
                )

        embed = Embed(
            description=f"Connected to: **{channel}**", color=Color.green()
        ).set_footer(text=f"Requested by {str(ctx.author)}")
        await ctx.reply(embed=embed)

    @commands.command(name="play", aliases=["sing"])
    async def play_(self, ctx, *, search: str):
        vc = ctx.voice_client

        if not vc:
            await ctx.invoke(self.connect_)

        player = self.get_player(ctx)

        # If download is False, source will be a dict which will be used later to regather the stream.
        # If download is True, source will be a discord.FFmpegPCMAudio with a VolumeTransformer.
        source = await YTDLSource.create_source(
            ctx, search, loop=self.bot.loop, download=False
        )

        await player.queue.put(source)

    @commands.command(name="pause")
    async def pause_(self, ctx):
        """Pause the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_playing():
            embed = Embed(
                description="No song is playing right now!", color=Color.red()
            )
            return await ctx.reply(embed=embed)
        elif vc.is_paused():
            return

        vc.pause()
        embed = Embed(
            description=f"**{str(ctx.author)}** paused the song!", color=Color.green()
        )
        await ctx.reply(embed=embed)

    @commands.command(name="resume")
    async def resume_(self, ctx):
        """Resume the currently paused song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = Embed(
                description="No song is playing right now!", color=Color.red()
            )
            return await ctx.reply(embed=embed)
        elif not vc.is_paused():
            return

        vc.resume()
        embed = Embed(
            description=f"**{str(ctx.author)}** paused the song!", color=Color.green()
        )
        await ctx.reply(embed=embed)

    @commands.command(name="skip")
    async def skip_(self, ctx):
        """Skip the song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = Embed(
                description="No song is playing right now!", color=Color.red()
            )
            return await ctx.reply(embed=embed)

        if vc.is_paused():
            pass
        elif not vc.is_playing():
            return

        vc.stop()
        embed = Embed(
            description=f"**{str(ctx.author)}** skipped the song!", color=Color.green()
        )
        await ctx.reply(embed=embed)

    @commands.command(name="queue", aliases=["q", "playlist"])
    async def queue_info(self, ctx):
        """Retrieve a basic queue of upcoming songs."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = Embed(
                description="I am not currently connected to a voice channel!",
                color=Color.red(),
            )
            return await ctx.reply(embed=embed)

        player = self.get_player(ctx)
        if player.queue.empty():
            embed = Embed(description="The queue is empty!", color=Color.dark_gold())
            return await ctx.reply(embed=embed)

        # Grab up to 5 entries from the queue...
        upcoming = list(itertools.islice(player.queue._queue, 0, 5))

        fmt = "\n".join(f'**`{_["title"]}`**' for _ in upcoming)
        embed = Embed(
            title=f"Upcoming - Next {len(upcoming)}",
            description=fmt,
            color=Color.og_blurple(),
        )

        await ctx.reply(embed=embed)

    @commands.command(
        name="now_playing", aliases=["np", "current", "currentsong", "playing"]
    )
    async def now_playing_(self, ctx):
        """Display information about the currently playing song."""
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = Embed(
                description="I am not currently connected to a voice channel!",
                color=Color.red(),
            )
            return await ctx.reply(embed=embed)

        player = self.get_player(ctx)
        if not player.current:
            embed = Embed(
                description="No song is playing right now!", color=Color.red()
            )
            return await ctx.reply(embed=embed)

        try:
            # Remove our previous now_playing message.
            await player.np.delete()
        except discord.HTTPException:
            pass

        embed = Embed(
            description=f"**Playing:** `{vc.source.title}`\n**Queued by:** `{vc.source.requester}`"
        )
        player.np = await ctx.reply(embed=embed)

    @commands.command(name="volume", aliases=["vol"])
    async def change_volume(self, ctx, *, vol: float):
        """Change the player volume.
        Parameters
        ------------
        volume: float or int [Required]
            The volume to set the player to in percentage. This must be between 1 and 100.
        """
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = Embed(
                description="I am not currently connected to a voice channel!",
                color=Color.red(),
            )
            return await ctx.reply(embed=embed)

        if not 0 < vol < 101:
            return await ctx.reply(
                embed=Embed(description=":x: Enter a value between 1 - 100")
            )

        player = self.get_player(ctx)

        if vc.source:
            vc.source.volume = vol / 100

        player.volume = vol / 100
        embed = Embed(description=f"**{ctx.author}**: Set the volume to **{vol}%**")
        await ctx.reply(embed=embed)

    @commands.command(name="stop", aliases=["leave"])
    async def stop_(self, ctx):
        """Stop the currently playing song and destroy the player.
        !Warning!
            This will destroy the player assigned to your guild, also deleting any queued songs and settings.
        """
        vc = ctx.voice_client

        if not vc or not vc.is_connected():
            embed = Embed(
                description="I am not currently connected to a voice channel!",
                color=Color.red(),
            )
            return await ctx.reply(embed=embed)

        await self.cleanup(ctx.guild)


async def setup(client):
    await client.add_cog(Music(client))
