import asyncio
import discord
import os

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.all()
intents.members = True

bot = discord.Bot(intents=intents,
                  description="What's The Flight Plan Bot granted by Tacojesus.",
                  debug_guilds=[181375626245046272])


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")


@bot.event
async def on_command_error(ctx, error):
    print(ctx, error)


@bot.command()
async def join(ctx):
    """Join your current voicechannel."""
    channel = ctx.author.voice.channel
    await channel.connect()
    await ctx.message.delete()


@bot.command()
async def leave(ctx):
    """Disconnect from current voicechannel."""
    await ctx.voice_client.disconnect()
    await ctx.message.delete()


@bot.event
async def on_voice_state_update(member, before, after):
    """Disconnects from voicechannel after 230s of inactivity."""
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
                await voice.disconnect()
            if not voice.is_connected():
                break


cogs_list = [
    'soundboard',
    'music',
    'streepje',
    'together',
    'calendar',
]

for cog in cogs_list:
    bot.load_extension(f'cogs.{cog}')

bot.run(TOKEN)
