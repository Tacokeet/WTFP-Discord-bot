import discord
import os
import datetime
from datetime import date
from discord.ext import commands, tasks
from dotenv import load_dotenv
from tinydb import TinyDB, Query


class Calendar(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bd_alert.start()
        if not os.path.exists(self.path_to_database):
            open(self.path_to_database, 'w+')
        self.User = Query()

    load_dotenv()
    path_to_database = str(os.getenv('CALENDAR_DB'))
    path_to_birthday_messages = str(os.getenv('BIRTHDAY_MESSAGES_PATH'))
    db = TinyDB(path_to_database)
    available_text_channels = []
    birthday_role = discord.role
    player_queue = []
    vc = discord.voice_client

    def play_next_bd_message(self):
        if len(self.player_queue) >= 1:
            self.player_queue.pop(0)
            try:
                self.vc.play(self.player_queue[0], after=lambda e: self.play_next_bd_message())
            except IndexError:
                return
        else:
            return

    async def play_bd_message(self, filename):
        if self.vc.is_playing():
            self.player_queue.append(discord.FFmpegPCMAudio(filename))
            return

        player = discord.FFmpegPCMAudio(filename)
        self.player_queue.append(player)
        self.vc.play(player, after=lambda e: self.play_next_bd_message())

    @discord.slash_command(name="mybd")
    async def my_bd(self, ctx, day: discord.Option(int), month: discord.Option(int), year: discord.Option(int)):
        """Add birthday D-M-Y (1-11-1996) to yourself"""
        try:
            date(year, month, day)
        except Exception as e:
            await ctx.send(e)

        if not self.db.search(self.User.name == ctx.author.id):
            self.db.insert(
                {'name': ctx.author.id, 'day': day, 'month': month, 'year': year, 'alert': False})
        else:
            self.db.update({'day': day, 'month': month, 'year': year}, self.User.name == ctx.author.id)
        await ctx.respond(
            "Noted! " + ctx.author.name + "'s birthday is on " + str(day) + "-" + str(month) + "-" + str(year))

    @discord.slash_command(name="notifybd")
    async def notify_bd(self, ctx):
        """Add yourself to the notify list to get notified when someone's birthday is within 2 weeks"""
        await ctx.author.add_roles(self.birthday_role)
        await ctx.respond("Added " + ctx.author.name + " to the notify list for birthdays.")

    @tasks.loop(hours=1)  # every hour
    async def bd_alert(self):
        now = datetime.datetime.now()
        two_weeks_from_now = now + datetime.timedelta(days=14)
        if now.hour == 8:  # should be 8
            for user in self.db:
                if user['day'] is now.day and user['month'] is now.month:
                    await self.available_text_channels[0].send(
                        self.birthday_role.mention + ' ' + "🎉 Happy Birthday " + self.bot.get_user(user['name']).mention + " You turned " + str(
                            now.year - user['year']) + " years old! 🎉")
                if user['day'] is two_weeks_from_now.day and user['month'] is two_weeks_from_now.month:
                    self.db.update({'alert': False}, self.User.name == user['name'])
                    await self.available_text_channels[0].send(self.birthday_role.mention + ' ' + self.bot.get_user(
                        user['name']).name + " their birthday will be in two weeks don't forget to buy some presents! 🎁")
        for guild in self.bot.guilds:
            for user in self.db:
                member = await guild.fetch_member(user['name'])
                if member.voice is not None and user['day'] is now.day and user['month'] is now.month and not user['alert']:
                    self.vc = await member.voice.channel.connect()
                    await self.play_bd_message(self.path_to_birthday_messages + 'hey.mp3')
                    await self.play_bd_message(self.path_to_birthday_messages + str(
                        user['name']) + '.mp3')
                    await self.play_bd_message(
                        self.path_to_birthday_messages + 'gefeliciteerd.mp3')
                    await self.play_bd_message(
                        self.path_to_birthday_messages + 'met.mp3')
                    await self.play_bd_message(
                        self.path_to_birthday_messages + 'je.mp3')
                    await self.play_bd_message(
                        self.path_to_birthday_messages + 'verjaardag.mp3')
                    self.db.update({'alert': True}, self.User.name == user['name'])

    @bd_alert.before_loop
    async def before_bd_alert(self):
        await self.bot.wait_until_ready()
        for server in self.bot.guilds:
            add_birthday_role = True

            for role in await server.fetch_roles():
                if role.name == 'Birthday':
                    self.birthday_role = role
                    add_birthday_role = False

            if add_birthday_role:
                self.birthday_role = await server.create_role(name="Birthday", colour=discord.Color.gold())

            for channel in server.channels:
                if str(channel.type) == 'text':
                    if channel.permissions_for(server.me).send_messages:
                        if "birthday" in channel.name:
                            self.available_text_channels.append(channel)


def setup(bot):
    bot.add_cog(Calendar(bot))
