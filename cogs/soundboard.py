import discord
import os
import asyncio
import eyed3
import math
from discord.ext import commands, pages
from discord.commands import Option, slash_command
from dotenv import load_dotenv
from discord.ui import InputText, Modal, Button


class Soundboard(commands.Cog):
    def __init__(self, bot):
        self.current_page = 0
        self.bot = bot
        self.update_soundlist()
        self.person = "Subveinz"

    load_dotenv()
    soundDir = []
    soundDirClean = []
    soundDict = {}
    sound_pages = {}

    path_to_soundfiles = str(os.getenv('SOUNDFILE_PATH'))

    def update_soundlist(self):
        """Updates the soundlist variables"""
        for file in sorted(os.listdir(self.path_to_soundfiles)):
            if file.__contains__('mp3'):
                artist = eyed3.load(self.path_to_soundfiles + '/' + file).tag.artist
                if artist not in self.soundDict:
                    self.soundDict[eyed3.load(self.path_to_soundfiles + '/' + file).tag.artist] = []
                    self.soundDict[eyed3.load(self.path_to_soundfiles + '/' + file).tag.artist].append(file)
                else:
                    self.soundDict[eyed3.load(self.path_to_soundfiles + '/' + file).tag.artist].append(file)
                self.soundDir.append(file)
                self.soundDirClean.append(file.replace('.mp3', '').lower())

    def get_pages(self):
        return self.pages

    @staticmethod
    def check(author):
        """Check if message author is the same author."""

        def inner_check(message):
            if message.author != author:
                return False
            return True

        return inner_check

    async def navigation(self, interaction):
        if interaction.custom_id == "prev":
            if self.current_page == 0:
                self.current_page = 0
            else:
                self.current_page -= 1
        elif interaction.custom_id == "next":
            if self.current_page == len(self.sound_pages[self.person]) - 1:
                self.current_page = self.current_page
            else:
                self.current_page += 1

        updated_view = discord.ui.View()
        options = []

        for artist in self.soundDict:
            options.append(discord.SelectOption(label=artist))
        user_select = discord.ui.Select(placeholder=self.person, options=options, row=4)
        user_select.callback = self.selection
        updated_view.add_item(user_select)

        previous_button = discord.ui.Button(emoji="⬅", row=3, custom_id='prev')
        next_button = discord.ui.Button(emoji="➡", row=3, custom_id='next')

        next_button.callback = self.navigation
        previous_button.callback = self.navigation

        updated_view.add_item(previous_button)
        updated_view.add_item(discord.ui.Button(
            label="{current_page}/{total_pages}".format(current_page=self.current_page + 1,
                                                        total_pages=len(self.sound_pages[self.person])), row=3,
            disabled=True))
        updated_view.add_item(next_button)
        for sound_button in self.sound_pages[self.person][self.current_page]:
            updated_view.add_item(sound_button)
        await interaction.response.edit_message(view=updated_view)

    async def selection(self, interaction):
        self.person = interaction.data['values'][0]
        updated_view = discord.ui.View()
        options = []

        self.current_page = 0

        for artist in self.soundDict:
            options.append(discord.SelectOption(label=artist))
        user_select = discord.ui.Select(placeholder=self.person, options=options, row=4)
        user_select.callback = self.selection
        updated_view.add_item(user_select)

        previous_button = discord.ui.Button(emoji="⬅", row=3, custom_id='prev')
        next_button = discord.ui.Button(emoji="➡", row=3, custom_id='next')

        next_button.callback = self.navigation
        previous_button.callback = self.navigation

        updated_view.add_item(previous_button)
        updated_view.add_item(
            discord.ui.Button(label="1/{total_pages}".format(total_pages=len(self.sound_pages[self.person])), row=3,
                              disabled=True))
        updated_view.add_item(next_button)
        for sound_button in self.sound_pages[self.person][self.current_page]:
            updated_view.add_item(sound_button)
        await interaction.response.edit_message(view=updated_view)

    @discord.slash_command(name='sblist')
    async def soundboard_list(self, ctx):
        # Basic view
        basic_view = discord.ui.View()
        options = []

        async def play_button(interaction):
            vc = ctx.voice_client
            vc.play(discord.FFmpegOpusAudio(source=self.path_to_soundfiles + '/' + interaction.custom_id + '.mp3'))
            await interaction.response.send_message('🎵 Playing: ' + interaction.custom_id, delete_after=1)

        # Generate sound button per 15 into list
        for artist in self.soundDict:
            self.sound_pages[artist] = []
            counter = 0
            temp_list = []
            for sound in self.soundDict[artist]:
                sound_button = discord.ui.Button(
                    label=sound.replace('.mp3', ''),
                    custom_id=sound.replace('.mp3', ''),
                    style=discord.ButtonStyle.gray,
                    disabled=False
                )
                sound_button.callback = play_button
                temp_list.append(sound_button)
                counter += 1
                if counter == 15:
                    self.sound_pages[artist].append(temp_list[:])
                    temp_list.clear()
                    counter = 0
            if temp_list:
                self.sound_pages[artist].append(temp_list[:])
                temp_list.clear()

        for artist in self.soundDict:
            options.append(discord.SelectOption(label=artist))
        user_select = discord.ui.Select(placeholder=self.person, options=options, row=4)
        user_select.callback = self.selection
        basic_view.add_item(user_select)

        previous_button = discord.ui.Button(emoji="⬅", row=3, custom_id='prev')
        next_button = discord.ui.Button(emoji="➡", row=3, custom_id='next')

        next_button.callback = self.navigation
        previous_button.callback = self.navigation

        basic_view.add_item(previous_button)

        basic_view.add_item(
            discord.ui.Button(label="1/{total_pages}".format(total_pages=len(self.sound_pages[self.person])), row=3,
                              disabled=True))
        basic_view.add_item(next_button)

        view = basic_view
        for sound_button in self.sound_pages[self.person][0]:
            view.add_item(sound_button)
        await ctx.send(view=view)

    async def get_sounds(self, ctx: discord.AutocompleteContext):
        """Returns a list of colors that begin with the characters entered so far."""
        return [sound for sound in self.soundDirClean if ctx.value in sound]

    @discord.slash_command(name='sb')
    async def soundboard(self, ctx: discord.ApplicationContext,
                         sound: Option(str, "Pick a sound!", autocomplete=get_sounds)):
        """Play the sound given in parameter, this can be the name or index in list."""
        vc = ctx.voice_client
        vc.play(discord.FFmpegOpusAudio(source=self.path_to_soundfiles + '/' + sound + '.mp3'))
        await ctx.respond("🎵 Playing: " + sound, delete_after=1)

    @discord.slash_command(name='reload')
    async def reload(self, ctx):
        """Reloads the soundboard."""
        self.update_soundlist()
        await ctx.respond(
            "All sounds are reloaded!"
        )
        await ctx.message.delete()

    @soundboard.before_invoke
    @soundboard_list.before_invoke
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
                await ctx.respond("Sorry I'm busy in another voice channel!")
                raise commands.CommandError("Author not in same voice channel.")
            else:
                await ctx.voice_client.disconnect()
                await ctx.author.voice.channel.connect()


def setup(bot):
    bot.add_cog(Soundboard(bot))
