import discord
from discord.ext import commands
import asyncio
import yt_dlp
from dotenv import load_dotenv
import os

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

ytdl_format_options = {
    'format': 'bestaudio/best',
    'quiet': True,
    'extractaudio': True,
    'audioformat': 'mp3',
    'outtmpl': '%(id)s.%(ext)s',
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'noplaylist': True,
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

@bot.event
async def on_message(message):
    await bot.process_commands(message)

@bot.command(name='join')
async def join(ctx):
    if ctx.author.voice:
        await ctx.author.voice.channel.connect()

@bot.command(name='play')
async def play(ctx, url):
    if not ctx.voice_client:
        await ctx.invoke(join)
    async with ctx.typing():
        player = await YTDLSource.from_url(url, stream=True)
        ctx.voice_client.play(player, after=lambda e: print(f'Player error: {e}') if e else None)
    await ctx.send(f'Now playing: {player.title}')

@bot.command(name='leave')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()

@bot.command(name='stop')
async def stop(ctx):
    if ctx.voice_client:
        ctx.voice_client.stop()
        song_queues[ctx.guild.id].clear()

@bot.command(name='pause')
async def pause(ctx):
    if ctx.voice_client and ctx.voice_client.is_playing():
        ctx.voice_client.pause()
        await ctx.send("Paused.")

@bot.command(name='resume')
async def resume(ctx):
    if ctx.voice_client and ctx.voice_client.is_paused():
        ctx.voice_client.resume()
        await ctx.send("Resumed.")

@bot.command(name='now')
async def now(ctx):
    song = current_song.get(ctx.guild.id)
    if song:
        await ctx.send(f"Currently playing: {song}")
    else:
        await ctx.send("No song is currently playing.")

token = os.getenv("BOT_TOKEN")
bot.run(token)
