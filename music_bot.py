import discord
from discord.ext import commands, tasks
import asyncio
import yt_dlp
from dotenv import load_dotenv
import os
from collections import deque
from datetime import datetime, timedelta, timezone
import base64

load_dotenv()

cookie_path = None
cookie_b64 = os.getenv("YOUTUBE_COOKIES_B64")

if cookie_b64:
    cookie_path = "cookies.txt"
    with open(cookie_path, "wb") as f:
        f.write(base64.b64decode(cookie_b64))

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
    'default_search': 'ytsearch'
}

if cookie_path:
    ytdl_format_options['cookiefile'] = cookie_path

ffmpeg_options = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)

song_queues = {}
current_song = {}
last_activity = {}

class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')

    @classmethod
    async def from_query(cls, query, *, loop=None, stream=True):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(query, download=not stream))
        if 'entries' in data:
            data = data['entries'][0]
        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options), data=data)

async def play_next(ctx):
    guild_id = ctx.guild.id
    if song_queues[guild_id]:
        next_query = song_queues[guild_id].popleft()
        player = await YTDLSource.from_query(next_query, stream=True)
        current_song[guild_id] = player.title
        last_activity[guild_id] = datetime.now(timezone.utc)
        ctx.voice_client.play(player, after=lambda e: bot.loop.create_task(play_next(ctx)))
        await ctx.send(f'Now playing: {player.title}')
    else:
        current_song[guild_id] = None

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')
    idle_check.start()

@tasks.loop(seconds=60)
async def idle_check():
    for guild in bot.guilds:
        vc = guild.voice_client
        if vc and not vc.is_playing() and not vc.is_paused():
            if guild.id in last_activity:
                if datetime.now(timezone.utc) - last_activity[guild.id] > timedelta(minutes=5):
                    await vc.disconnect()
                    song_queues[guild.id].clear()
                    current_song[guild.id] = None
                    print(f'Disconnected from {guild.name} due to inactivity.')

@bot.command(name='join')
async def join(ctx):
    if ctx.author.voice:
        await ctx.author.voice.channel.connect()
        guild_id = ctx.guild.id
        song_queues.setdefault(guild_id, deque())
        current_song.setdefault(guild_id, None)
        last_activity[guild_id] = datetime.now(timezone.utc)
    else:
        await ctx.send("You're not in a voice channel!")

@bot.command(name='play')
async def play(ctx, *, query):
    if not ctx.voice_client:
        await ctx.invoke(join)
    guild_id = ctx.guild.id
    if ctx.voice_client.is_playing() or ctx.voice_client.is_paused():
        song_queues[guild_id].append(query)
        await ctx.send(f"Added to queue: {query}")
    else:
        song_queues[guild_id].appendleft(query)
        await play_next(ctx)

@bot.command(name='leave')
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        song_queues[ctx.guild.id].clear()
        current_song[ctx.guild.id] = None

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

@bot.command(name='skip')
async def skip(ctx):
    voice = ctx.voice_client
    if not voice or not voice.is_playing():
        await ctx.send("Nothing is currently playing.")
        return

    await ctx.send("Skipping current song...")
    voice.stop()

token = os.getenv("BOT_TOKEN")
bot.run(token)
