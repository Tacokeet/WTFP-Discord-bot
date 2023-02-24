import asyncio
import discord
import yt_dlp as youtube_dl
import validators
from discord.ext import commands
from youtubesearchpython import VideosSearch


class Music(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    ytdl_format_options = {
        'format': 'bestaudio/best',
        'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
        'restrictfilenames': True,
        'noplaylist': True,
        'nocheckcertificate': True,
        'ignoreerrors': False,
        'logtostderr': False,
        'quiet': True,
        'no_warnings': True,
        'default_search': 'auto',
        'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
    }
    ffmpeg_options = {
        'options': '-vn -ar 48000 -af loudnorm=I=-28:LRA=7:TP=-1.5',
        'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5'
    }
    ytdl = youtube_dl.YoutubeDL(ytdl_format_options, )
    song_queue = []
    player_queue = []

    def play_next(self, ctx):
        if len(self.player_queue) >= 1:
            self.player_queue.pop(0)
            self.song_queue.pop(0)
            try:
                ctx.voice_client.play(self.player_queue[0], after=lambda e: self.play_next(ctx))
            except IndexError:
                return
        else:
            return

    async def from_url(self, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(url, download=not stream))
        filename = data['url'] if stream else self.ytdl.prepare_filename(data)
        self.song_queue.append(data['title'])
        return discord.FFmpegPCMAudio(filename, **self.ffmpeg_options)

    @discord.slash_command(name="p")
    async def p(self, ctx, *, url):
        """Streams from an url or searches for song name"""
        return await self.play(ctx, url=url)

    @discord.slash_command(name="removesong")
    async def remove_song(self, ctx, index: int):
        """Remove song from playlist at index"""
        await ctx.respond("🎶 Removed: " + self.song_queue[index - 1] + " from the queue")
        self.song_queue.pop(index - 1)
        self.player_queue.pop(index - 1)

    @discord.slash_command(name="playlist")
    async def playlist(self, ctx):
        """Lists the current playlist"""
        if len(self.song_queue) >= 1:
            playlist_string = "```ini\n"
            for x, y in enumerate(self.song_queue):
                playlist_string += '[' + str(x + 1) + ']' + " " + str(y) + '\n'

            playlist_string += "```"
            await ctx.respond(playlist_string)
        else:
            await ctx.respond("🎶 Playlist is empty you an add song by using the command !p <url> or !play <url>")

    @discord.slash_command(name="play")
    async def play(self, ctx, *, url):
        """Streams from an url or searches for song name"""
        vc = ctx.voice_client
        if not validators.url(url):
            search_result = VideosSearch(url, limit=1)
            url = search_result.result()['result'][0]['link']

        if vc.is_playing():
            self.player_queue.append(await self.from_url(url, loop=self.bot.loop, stream=True))
            await ctx.respond("🎶 Added: " + self.song_queue[-1] + " to the playlist")
            return

        player = await self.from_url(url, loop=self.bot.loop, stream=True)
        self.player_queue.append(player)
        ctx.voice_client.play(player, after=lambda e: self.play_next(ctx))
        await ctx.respond("🎶 Now Playing: " + self.song_queue[-1])

    @discord.slash_command(name="skip")
    async def skip(self, ctx):
        """Skips the current song"""
        ctx.voice_client.stop()
        await ctx.respond("⏭ Skipped current song!!", delete_after=1)

    @discord.slash_command(name="stop")
    async def stop(self, ctx):
        """Stops the player"""
        self.song_queue.clear()
        self.player_queue.clear()
        ctx.voice_client.stop()
        await ctx.respond("🛑 Stopped playing music!", delete_after=1)

    @p.before_invoke
    @play.before_invoke
    @skip.before_invoke
    @stop.before_invoke
    @remove_song.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.respond("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.channel.id is not ctx.author.voice.channel.id:
            if not ctx.author.voice:
                await ctx.respond("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
            if ctx.voice_client.is_playing():
                await ctx.respond("Sorry I'm busy singing songs in another voice channel!")
                raise commands.CommandError("Author not in same voice channel.")
            else:
                await ctx.voice_client.disconnect()
                await ctx.author.voice.channel.connect()


def setup(bot):
    bot.add_cog(Music(bot))
