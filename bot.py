import asyncio
import math
import time
import discord
import eyed3
import os
from os import path

from discord.ext import commands
from dotenv import load_dotenv

from tinydb import TinyDB, Query
from tinydb.operations import increment

if not path.exists('streepjesDB.json'):
    open('streepjesDB.json', 'w+')
db = TinyDB('streepjesDB.json')
User = Query()
streepjes_messages = {}

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.members = True

client = discord.Client()
bot = commands.Bot(command_prefix='!', intents=intents)

soundDir = []
soundDict = {}
for file in os.listdir('F:/GoogleDrive/Soundtest'):
    if file.__contains__('mp3'):
        soundDict[file] = eyed3.load('F:/GoogleDrive/Soundtest/' + file).tag.artist
        soundDir.append(file)


def check(author):
    """Check if message author is the same author."""

    def inner_check(message):
        if message.author != author:
            return False
        try:
            int(message.content)
            return True
        except ValueError:
            return False

    return inner_check


def print_table(data, cols, wide):
    """Prints formatted data on columns of given width."""
    n, r = divmod(len(data), cols)
    pat = '{{:{}}}'.format(wide)
    line = '\n'.join(pat * cols for _ in range(n))
    return line.format(*data)


def search_soundlist(search, sounddict):
    """Searcher through dict.values and gets all the items containing search."""
    clean_soundlist = [x.lower().strip('.mp3') for x in list(sounddict.keys())]
    results = []
    for sound in clean_soundlist:
        if search in sound:
            results.append(clean_soundlist.index(sound))
    return results


def create_soundboardlist(sound_dict):
    sb_list_messages = []
    tables = []
    float_sep = math.modf(len(sound_dict) / 40)
    keys_list = list(sound_dict)
    for amount_table in range(round(float_sep[1]) + 1):
        temptable = []
        lefttable = []
        if len(sound_dict) >= 20:
            for x in range(20):
                if (40 * amount_table + x + 20) >= len(sound_dict):
                    lefttable.append(str('[' + str(40 * amount_table + x + 1) + '] ' + list(sound_dict.keys())[
                        40 * amount_table + x].strip('.mp3') + ' by: ' + sound_dict[
                                             list(sound_dict.keys())[40 * amount_table + x]]))
                    continue
                temptable.append(str(
                    '[' + str(40 * amount_table + x + 1) + '] ' + list(sound_dict.keys())[
                        40 * amount_table + x].strip('.mp3') + ' by: ' +
                    sound_dict[list(sound_dict.keys())[40 * amount_table + x]]))
                temptable.append(str('[' + str(40 * amount_table + x + 21) + '] ' + list(sound_dict.keys())[
                    40 * amount_table + x + 20].strip('.mp3') + ' by: ' + sound_dict[
                                         list(sound_dict.keys())[40 * amount_table + x + 20]]))
            tables.append(temptable)
        else:
            for x in range(len(sound_dict)):
                if (40 * amount_table + x + 20) >= len(sound_dict):
                    lefttable.append(str('[' + str(40 * amount_table + x + 1) + '] ' + list(sound_dict.keys())[
                        40 * amount_table + x].strip('.mp3') + ' by: ' + sound_dict[
                                             list(sound_dict.keys())[40 * amount_table + x]]))
                    continue
                temptable.append(str(
                    '[' + str(40 * amount_table + x + 1) + '] ' + list(sound_dict.keys())[
                        40 * amount_table + x].strip('.mp3') + ' by: ' +
                    sound_dict[list(sound_dict.keys())[40 * amount_table + x]]))
                temptable.append(str('[' + str(40 * amount_table + x + 21) + '] ' + list(sound_dict.keys())[
                    40 * amount_table + x + 20].strip('.mp3') + ' by: ' + sound_dict[
                                         list(sound_dict.keys())[40 * amount_table + x + 20]]))
            tables.append(temptable)

    strlefttable = "\n"
    for table in lefttable:
        strlefttable += table + '\n'
    for table in tables:
        if table is tables[-1]:
            sb_list_messages.append("```ini\n" + print_table(table, 2, 43) + strlefttable + "\n```")
        else:
            sb_list_messages.append("```ini\n" + print_table(table, 2, 43) + "\n```")
    return sb_list_messages


def create_search_soundlist(searchresults, sounddict):
    """Creates a list to show the search results."""
    search_soundDict = {}
    for result in searchresults:
        search_soundDict[list(sounddict.keys())[result].strip('.mp3')] = sounddict[list(sounddict.keys())[result]]
    return create_soundboardlist(search_soundDict), search_soundDict


async def get_response(ctx, sounddict):
    try:
        msg = await bot.wait_for('message', check=check(ctx.author), timeout=25)
    except asyncio.TimeoutError:
        await ctx.message.channel.send('You took to long :sleeping:')
        return
    if str(msg.content) == "cancel":
        return
    msgnumber = int(msg.content)
    if msgnumber - 1 > len(sounddict):
        await ctx.message.channel.send('Number not in the list please try again')
        return await get_response(ctx, sounddict)
    return msgnumber


@bot.event
async def on_ready():
    print('Bot online!')


@bot.event
async def on_reaction_add(reaction, user):
    if reaction.emoji == "👍":
        if reaction.message.id in streepjes_messages.keys():
            if user.id == streepjes_messages[reaction.message.id][1]:
                await reaction.remove(user)
            elif reaction.count == 3:
                if reaction.message.id in streepjes_messages.keys():
                    if not db.search(User.name == streepjes_messages[reaction.message.id][0]):
                        db.insert({'name': streepjes_messages[reaction.message.id][0], 'streepjes': 1})
                    else:
                        db.update(increment('streepjes'), User.name == streepjes_messages[reaction.message.id][0])
                    await reaction.message.channel.send(
                        "{} now has {} streepje(s)".format(
                            bot.get_user(streepjes_messages[reaction.message.id][0]).name, db.search(
                                User.name == streepjes_messages[reaction.message.id][0])[0]['streepjes'])
                    )


@bot.command(name="reload")
async def commands(ctx):
    """Reloads the soundboard."""
    await ctx.message.channel.send(
        "All sounds are reloaded!"
    )

    for file in os.listdir('F:/GoogleDrive/Soundtest'):
        if file.__contains__('mp3'):
            soundDict[file] = eyed3.load('F:/GoogleDrive/Soundtest/' + file).tag.artist
            soundDir.append(file)


@bot.command(name="streepjeslist")
async def commands(ctx):
    message = ""
    for person in db.all():
        message += "{person} : {streepjes}\n".format(person=bot.get_user(person['name']).name,
                                                     streepjes=person['streepjes'])
    await ctx.message.channel.send(message)


@bot.command(name="streepje")
async def commands(ctx, person):
    """Gives streepjes to a user."""
    if ctx.message.author.permissions_in(ctx.message.channel).ban_members:
        if not db.search(User.name == ctx.message.mentions[0].id):
            db.insert({'name': ctx.message.mentions[0].id, 'streepjes': 1})
        else:
            db.update(increment('streepjes'), User.name == ctx.message.mentions[0].id)
        print(ctx.message.mentions[0].name)
        print(str(db.search(User.name == int(ctx.message.mentions[0].id))[0]['streepjes']))
        await ctx.message.channel.send(
            "{Person} now has {streepjes} streepje(s)".format(Person=ctx.message.mentions[0].name,
                                                              streepjes=str(db.search(
                                                                  User.name == int(ctx.message.mentions[0].id))[0][
                                                                                'streepjes'])))
    else:
        await ctx.message.channel.send(
            "{Author} wants to add a streepje to {Person}. \n 3 👍 are needed!".format(
                Author=ctx.message.author.mention, Person=person)
        )
        messages = await ctx.message.channel.history(limit=10).flatten()
        await messages[0].add_reaction(emoji='👍')
        streepjes_messages[messages[0].id] = [ctx.message.mentions[0].id, ctx.message.author.id]


@bot.command(name='sblist')
async def soundboardlist(ctx):
    """Shows all sounds that are available and if you type a number it will the the associate sound."""
    for sb_messages in create_soundboardlist(soundDict):
        await ctx.message.channel.send(
            sb_messages
        )
    await ctx.message.channel.send(
        "Type a number to make a choice or type cancel to stop"
    )
    response = await get_response(ctx, soundDict)
    await soundboard(ctx, soundDir[response - 1].strip('.mp3'))


@bot.command(name='sbsearch')
async def soundboardsearch(ctx, search):
    """Search trough all the available sounds and show them, then type a number to play the sound."""
    results = search_soundlist(search.lower(), soundDict)
    if results:
        css = create_search_soundlist(results, soundDict)
        for result_list in css[0]:
            await ctx.message.channel.send(
                result_list
            )
        await ctx.message.channel.send(
            "Type a number to make a choice or type cancel to stop"
        )
        response = await get_response(ctx, css[1])
        await soundboard(ctx, soundDir[results[response - 1]].strip('.mp3'))
    else:
        await ctx.message.channel.send(
            "Could not find any sounds matching that description")


@bot.command(name="sb")
async def soundboard(ctx, sound):
    """Play the sound given in parameter, this can be the name or index in list."""
    # Gets voice channel of message author
    voice_channel = ctx.author.voice.channel
    if voice_channel is not None:
        if not bot.voice_clients:
            vc = await voice_channel.connect()
        else:
            for vc_client in bot.voice_clients:
                if ctx.author.voice.channel.id == vc_client.channel.id:
                    vc = vc_client
                else:
                    if ctx.author.voice.channel.guild == vc_client.guild:
                        await vc_client.move_to(voice_channel)
                        vc = vc_client
        if sound.isdigit():
            vc.play(discord.FFmpegOpusAudio(source="F:/GoogleDrive/Soundtest/" + soundDir[int(sound) - 1]))
        else:
            vc.play(discord.FFmpegOpusAudio(source="F:/GoogleDrive/Soundtest/" + sound + ".mp3"))
        while vc.is_playing():
            time.sleep(.1)
        vc.stop()
    else:
        await ctx.message.channel.send(
            str(ctx.author.name) + "is not in a channel."
        )
    await ctx.message.delete()


@bot.command()
async def join(ctx):
    """Join your current voicechannel."""
    channel = ctx.author.voice.channel
    await channel.connect()


@bot.command()
async def leave(ctx):
    """Disconnect from current voicechannel."""
    await ctx.voice_client.disconnect()


bot.run(TOKEN)
