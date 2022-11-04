import asyncio
import discord
import os
import logging

from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.all()
# intents.members = True

bot = discord.Bot(intents=intents,
                  description="What's The Flight Plan Bot granted by Tacojesus.",
                  debug_guilds=[181375626245046272]
                  # debug_guilds=[181374963427704833]
                  )

path_to_soundfiles = str(os.getenv('SOUNDFILE_PATH'))


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")


@bot.event
async def on_command_error(ctx, error):
    print(ctx, error)


@bot.command()
async def join(ctx):
    """Join your current voice-channel."""
    channel = ctx.author.voice.channel
    await ctx.respond("Joining your voicec-hannel! ", delete_after=1)
    await channel.connect()


@bot.command()
async def leave(ctx):
    """Disconnect from current voice-channel."""
    await ctx.respond("Leaving your voice-channel! ", delete_after=1)
    await ctx.voice_client.disconnect()


def my_after(vc):
    coro = vc.disconnect()
    fut = asyncio.run_coroutine_threadsafe(coro, bot.loop)
    try:
        fut.result()
    except Exception as bex:
        print(bex)
        pass


@bot.event
async def on_voice_state_update(member, before, after):
    """Disconnects from voice-channel after 230s of inactivity."""

    if not member.id == bot.user.id:
        return
    elif before.channel is None:
        voice = after.channel.guild.voice_client
        time = 0
        while True:
            await asyncio.sleep(1)
            time = time + 1
            if voice.is_playing() and not voice.is_paused():
                time = 0
            if time == 230:
                if os.path.isfile(path_to_soundfiles + '/Marokaan uit bitch.mp3'):
                    voice.play(discord.FFmpegOpusAudio(source=path_to_soundfiles + '/Marokaan uit bitch.mp3'),
                               after=lambda e: my_after(voice))
                else:
                    await voice.disconnect()
            if not voice.is_connected():
                break


cogs_list = [
    'soundboard',
    'music',
    'streepje',
    'together',
    'calendar',
    'spotify',
]

for cog in cogs_list:
    bot.load_extension(f'cogs.{cog}')

bot.run(TOKEN)
