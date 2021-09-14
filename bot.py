import asyncio
import math
import discord
import eyed3
import os
import youtube_dl
import validators
from os import path
from discord.ext import commands, tasks
from dotenv import load_dotenv
from tinydb import TinyDB, Query
from tinydb.operations import increment
from discordTogether import DiscordTogether
from youtubesearchpython import VideosSearch

load_dotenv()
"""Database variables"""
path_to_database = str(os.getenv('STREEPJES_DB'))

if not path.exists(path_to_database):
    open(path_to_database, 'w+')

db = TinyDB(path_to_database)
User = Query()
streepjes_messages = {}

"""If dotenv is used it is loaded in here if not replace DISCORD_TOKEN with load_dotenv(find_dotenv())
yours"""
TOKEN = os.getenv('DISCORD_TOKEN')

"""Declaring intent so that I can search through members"""
intents = discord.Intents.default()
intents.members = True

"""Setting up bot"""
bot = commands.Bot(command_prefix=commands.when_mentioned_or("!"), intents=intents,
                   description="What's The Flight Plan Bot granted by Tacojesus.")

"""Soundlist variables"""
soundDir = []
soundDict = {}
path_to_soundfiles = str(os.getenv('SOUNDFILE_PATH'))

"""Jeopardy variables"""
teams = []
buzer = False

"""Youtube dl variables"""
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
    'options': '-vn'
}
ytdl = youtube_dl.YoutubeDL(ytdl_format_options)
song_queue = []
player_queue = []

"""Discord Together variables"""
togetherControl = DiscordTogether(bot)


def update_soundlist():
    """Updates the soundlist variables"""
    for file in sorted(os.listdir(path_to_soundfiles)):
        if file.__contains__('mp3'):
            soundDict[file] = eyed3.load(path_to_soundfiles + '/' + file).tag.artist
            soundDir.append(file)


def check(author):
    """Check if message author is the same author."""

    def inner_check(message):
        if message.author != author:
            return False
        return True

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
    """Creates string that shows all the avaible sounds"""
    sb_list_messages = []
    tables = []
    float_sep = math.modf(len(sound_dict) / 30)
    keys_list = list(sound_dict)
    for amount_table in range(round(float_sep[1]) + 1):
        temptable = []
        lefttable = []
        if len(sound_dict) >= 20:
            for x in range(20):
                if (30 * amount_table + x + 20) >= len(sound_dict):
                    lefttable.append(str('[' + str(30 * amount_table + x + 1) + '] ' + list(sound_dict.keys())[
                        30 * amount_table + x].strip('.mp3') + ' by: ' + sound_dict[
                                             list(sound_dict.keys())[30 * amount_table + x]]))
                    continue
                temptable.append(str(
                    '[' + str(30 * amount_table + x + 1) + '] ' + list(sound_dict.keys())[
                        30 * amount_table + x].strip('.mp3') + ' by: ' +
                    sound_dict[list(sound_dict.keys())[30 * amount_table + x]]))
                temptable.append(str('[' + str(30 * amount_table + x + 21) + '] ' + list(sound_dict.keys())[
                    30 * amount_table + x + 20].strip('.mp3') + ' by: ' + sound_dict[
                                         list(sound_dict.keys())[30 * amount_table + x + 20]]))
            tables.append(temptable)
        else:
            for x in range(len(sound_dict)):
                if (30 * amount_table + x + 20) >= len(sound_dict):
                    lefttable.append(str('[' + str(30 * amount_table + x + 1) + '] ' + list(sound_dict.keys())[
                        30 * amount_table + x].strip('.mp3') + ' by: ' + sound_dict[
                                             list(sound_dict.keys())[30 * amount_table + x]]))
                    continue
                temptable.append(str(
                    '[' + str(30 * amount_table + x + 1) + '] ' + list(sound_dict.keys())[
                        30 * amount_table + x].strip('.mp3') + ' by: ' +
                    sound_dict[list(sound_dict.keys())[30 * amount_table + x]]))
                temptable.append(str('[' + str(30 * amount_table + x + 21) + '] ' + list(sound_dict.keys())[
                    30 * amount_table + x + 20].strip('.mp3') + ' by: ' + sound_dict[
                                         list(sound_dict.keys())[30 * amount_table + x + 20]]))
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
        return False
    msgnumber = int(msg.content)
    if msgnumber - 1 > len(sounddict):
        await ctx.message.channel.send('Number not in the list please try again')
        return await get_response(ctx, sounddict)
    return msgnumber


@bot.event
async def on_ready():
    print('Logged in as {0} ({0.id})'.format(bot.user))
    print('------')


@bot.event
async def on_command_error(ctx, exception):
    if exception.__class__ == discord.ext.commands.errors.MissingRequiredArgument:
        if str(ctx.command) == "sb":
            await ctx.message.channel.send("Please specify a number or the full name.")
        elif str(ctx.command) == "sbsearch":
            await ctx.message.channel.send("Please give a argument to search for.")
        elif str(ctx.command) == "streepje":
            await ctx.message.channel.send("Please specify a user to receive a streepje.")


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
async def reload(ctx):
    """Reloads the soundboard."""
    update_soundlist()
    await ctx.message.channel.send(
        "All sounds are reloaded!"
    )
    await ctx.message.delete()


@bot.command(name="mkteam")
async def make_team(ctx, personone, persontwo, teamname, soundid):
    """make team for Jeopardy."""
    if ctx.message.author.permissions_in(ctx.message.channel).ban_members:
        await ctx.message.channel.send(
            "{personone} and {persontwo} are now team: {teamname} with soundID: {soundid}.".format(
                personone=ctx.message.mentions[0].name,
                persontwo=ctx.message.mentions[1].name, teamname=str(teamname), soundid=str(soundid)))
        teams.append([ctx.message.mentions[0].id, ctx.message.mentions[1].id, teamname, soundid])
    else:
        await ctx.message.channel.send(
            "Only admins are allowed to create teams."
        )


@bot.command(name="reset")
async def reset_question(ctx):
    """Reset question for Jeopardy."""
    global buzer
    if ctx.message.author.permissions_in(ctx.message.channel).ban_members:
        buzer = False
        await ctx.message.channel.send(
            "Buzzers are reset!"
        )
    else:
        await ctx.message.channel.send(
            "Only admins are allowed to reset the question teams."
        )


@bot.command(name="clrteams")
async def clear_team(ctx):
    """clears teams for Jeopardy."""
    await ctx.message.channel.send(
        "Cleared all Jeopardy teams."
    )
    teams.clear()


@bot.command(name="listteams")
async def clear_team(ctx):
    """lists all the teams for Jeopardy."""
    allteams = ""
    for team in teams:
        allteams += "Team : " + team[2] + " with members: " + bot.get_user(team[0]).name + " and " + bot.get_user(
            team[1]).name + " with buzzer sound: " + team[3] + '\n'
    await ctx.message.channel.send(
        allteams
    )


@bot.command(name="buz")
async def call(ctx):
    """Buzzez in for Jeopardy."""
    global buzer

    if teams:
        if buzer:
            await ctx.message.channel.send(
                " Buzzers are disabled waiting for reset!"
            )
            return
        for team in teams:
            if ctx.message.author.id in team:
                await ctx.message.channel.send(
                    team[2] + " Buzzed in!"
                )
                buzer = True
                await soundboard(ctx, team[3])
                return
        await ctx.message.channel.send(
            ctx.message.author.name + " is not in a team!"
        )
        return
    else:
        await ctx.message.channel.send(
            "There aren't any teams, please make some teams."
        )


@bot.command(name="streepjeslist")
async def streepjeslist(ctx):
    """Shows the current standing of streepjes."""
    message = ""
    for person in db.all():
        message += "{person} : {streepjes}\n".format(person=bot.get_user(person['name']).name,
                                                     streepjes=person['streepjes'])
    if message == "":
        await ctx.message.channel.send("There aren't any streepjes in the database.")
    else:
        await ctx.message.channel.send(message)
    await ctx.message.delete()


@bot.command(name="streepje")
async def streepje(ctx, person):
    """Gives streepjes to a user."""
    if ctx.message.author.permissions_in(ctx.message.channel).ban_members:
        if not db.search(User.name == ctx.message.mentions[0].id):
            db.insert({'name': ctx.message.mentions[0].id, 'streepjes': 1})
        else:
            db.update(increment('streepjes'), User.name == ctx.message.mentions[0].id)
        await ctx.message.channel.send(
            "{Person} now has {streepjes} streepje(s)".format(Person=ctx.message.mentions[0].name,
                                                              streepjes=str(db.search(
                                                                  User.name == int(ctx.message.mentions[0].id))[0][
                                                                                'streepjes'])))
    else:
        await ctx.message.channel.send(
            "{Author} wants to add a streepje to {Person}.\n3 👍 are needed!".format(
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
    if not response:
        return
    try:
        await soundboard(ctx, soundDir[response - 1].strip('.mp3'))
    except AttributeError:
        await ctx.message.channel.send(
            "You are currently not in a voice channel!\nPlease join a voice channel."
        )
    await ctx.message.delete()


@bot.command(name='sbsearch')
async def soundboardsearch(ctx, search):
    """Search trough all the available sounds and show them, then type a number to play the sound."""
    try:
        voice_channel = ctx.author.voice.channel
    except AttributeError:
        await ctx.message.channel.send(
            "Join a voice channel to use this command!"
        )
        await ctx.message.delete()
        return
    results = search_soundlist(search.lower(), soundDict)
    if results:
        css = create_search_soundlist(results, soundDict)
        for result_list in css[0]:
            await ctx.message.channel.send(
                result_list
            )
        await ctx.message.delete()
        await ctx.message.channel.send(
            "Type a number to make a choice or type cancel to stop"
        )
        response = await get_response(ctx, css[1])
        if not response:
            return

        try:
            await soundboard(ctx, soundDir[results[response - 1]].strip('.mp3'))
        except AttributeError:
            await ctx.message.channel.send(
                "You are currently not in a voice channel!\nPlease join a voice channel."
            )
    else:
        await ctx.message.channel.send(
            "Could not find any sounds matching that description")


@bot.command(name="sb")
async def soundboard(ctx, sound):
    """Play the sound given in parameter, this can be the name or index in list."""
    try:
        voice_channel = ctx.author.voice.channel
    except AttributeError:
        await ctx.message.channel.send(
            "Join a voice channel to use this command!"
        )
        await ctx.message.delete()

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
            vc.play(discord.FFmpegOpusAudio(source=path_to_soundfiles + '/' + soundDir[int(sound) - 1]))
        else:
            vc.play(discord.FFmpegOpusAudio(source=path_to_soundfiles + '/' + sound + ".mp3"))
        await ctx.message.delete()


def play_next(ctx):
    if len(player_queue) >= 1:
        player_queue.pop(0)
        song_queue.pop(0)
        try:
            ctx.voice_client.play(player_queue[0], after=lambda e: play_next(ctx))
        except IndexError:
            return
    else:
        return


async def from_url(url, *, loop=None, stream=False):
    loop = loop or asyncio.get_event_loop()
    data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))
    filename = data['url'] if stream else ytdl.prepare_filename(data)
    song_queue.append(data['title'])
    return discord.FFmpegPCMAudio(filename, **ffmpeg_options)


@bot.command(name="p")
async def p(ctx, *, url):
    """Streams from a url"""
    return await play(ctx, url=url)


@bot.command(name="removesong")
async def remove_song(ctx, index: int):
    """Remove song from playlist at index"""
    await ctx.send("🎶 Removed: " + song_queue[index - 1] + " from the queue")
    song_queue.pop(index - 1)
    player_queue.pop(index - 1)


@bot.command(name="playlist")
async def playlist(ctx):
    """Lists the current playlist"""
    if len(song_queue) >= 1:
        playlist_string = "```ini\n"
        for x, y in enumerate(song_queue):
            playlist_string += '[' + str(x + 1) + ']' + " " + str(y) + '\n'

        playlist_string += "```"
        await ctx.send(playlist_string)
    else:
        await ctx.send("🎶 Playlist is empty you an add song by using the command !p <url> or !play <url>")


@bot.command(name="play")
async def play(ctx, *, url):
    """Streams from a url"""
    try:
        voice_channel = ctx.author.voice.channel
    except AttributeError:
        await ctx.message.channel.send(
            "Join a voice channel to use this command!"
        )
        await ctx.message.delete()
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
    if not validators.url(url):
        search_result = VideosSearch(url, limit=1)
        url = search_result.result()['result'][0]['link']

    if vc.is_playing():
        player_queue.append(await from_url(url))
        await ctx.send("🎶 Added: " + song_queue[-1] + " to the playlist")

        return

    player = await from_url(url, loop=bot.loop, stream=True)
    player_queue.append(player)
    ctx.voice_client.play(player, after=lambda e: play_next(ctx))
    await ctx.send("🎶 Now Playing: " + song_queue[-1])


@bot.command(name="skip")
async def skip(ctx):
    """Skips the current song"""
    if ctx.voice_client is None:
        return await ctx.send("Not connected to a voice channel.")

    ctx.voice_client.stop()


@bot.command(name="stop")
async def stop(ctx):
    """Stops the player"""
    if ctx.voice_client is None:
        return await ctx.send("Not connected to a voice channel.")

    song_queue.clear()
    player_queue.clear()
    ctx.voice_client.stop()


@bot.command('together')
async def together(ctx, type):
    """Together: youtube, poker, chess, betrayal, fishing"""
    link = await togetherControl.create_link(ctx.author.voice.channel.id, str(type))
    await ctx.send(f"Click the blue link!\n{link}")


@tasks.loop(seconds=60)
async def background_is_playing():
    if bot.voice_clients:
        for vc in bot.voice_clients:
            if not vc.is_playing():
                await vc.disconnect()


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


@background_is_playing.before_loop
async def before_my_task():
    await bot.wait_until_ready()  # wait until the bot logs in


background_is_playing.start()
update_soundlist()
bot.run(TOKEN)
