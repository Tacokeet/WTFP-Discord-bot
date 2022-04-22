import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
from tinydb import TinyDB, Query
from tinydb.operations import increment


class Streepje(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        if not os.path.exists(self.path_to_database):
            open(self.path_to_database, 'w+')
        self.User = Query()

    load_dotenv()
    path_to_database = str(os.getenv('STREEPJES_DB'))
    db = TinyDB(path_to_database)

    streepjes_messages = {}
    available_text_channels = []

    @discord.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.emoji == "👍":
            if reaction.message.id in self.streepjes_messages.keys():
                if user.id == self.streepjes_messages[reaction.message.id][1]:
                    await reaction.remove(user)
                elif reaction.count == 3:
                    if reaction.message.id in self.streepjes_messages.keys():
                        if not self.db.search(self.User.name == self.streepjes_messages[reaction.message.id][0]):
                            self.db.insert({'name': self.streepjes_messages[reaction.message.id][0], 'streepjes': 1})
                        else:
                            self.db.update(increment('streepjes'),
                                           self.User.name == self.streepjes_messages[reaction.message.id][0])
                        await reaction.message.channel.send(
                            "{} now has {} streepje(s)".format(
                                self.bot.get_user(self.streepjes_messages[reaction.message.id][0]).name, self.db.search(
                                    self.User.name == self.streepjes_messages[reaction.message.id][0])[0]['streepjes']))

    @discord.slash_command(name="streepjeslist")
    async def streepjeslist(self, ctx):
        """Shows the current standing of streepjes."""
        message = ""
        for person in self.db.all():
            message += "{person} : {streepjes}\n".format(person=self.bot.get_user(person['name']).name,
                                                         streepjes=person['streepjes'])
        if message == "":
            await ctx.message.channel.send("There aren't any streepjes in the database.")
        else:
            await ctx.message.channel.send(message)
        await ctx.message.delete()

    @discord.slash_command(name="streepje")
    async def streepje(self, ctx: discord.ApplicationContext, person: discord.Member):
        """Gives streepjes to a user."""
        # if ctx.message.author.permissions_in(ctx.message.channel).ban_members:
        #     if not self.db.search(self.User.name == ctx.message.mentions[0].id):
        #         self.db.insert({'name': ctx.message.mentions[0].id, 'streepjes': 1})
        #     else:
        #         self.db.update(increment('streepjes'), self.User.name == ctx.message.mentions[0].id)
        #     await ctx.message.channel.send(
        #         "{Person} now has {streepjes} streepje(s)".format(Person=ctx.message.mentions[0].name,
        #                                                           streepjes=str(self.db.search(
        #                                                               self.User.name == int(
        #                                                                   ctx.message.mentions[0].id))[0][
        #                                                                             'streepjes'])))
        # else:
        respond = await ctx.respond(
            "{Author} wants to add a streepje to {Person}.\n3 👍 are needed!".format(
                Author=ctx.author.mention, Person=person.mention))
        messages = await ctx.channel.history(limit=10).flatten()
        await messages[0].add_reaction(emoji='👍')
        self.streepjes_messages[messages[0].id] = [person.id, ctx.author.id]


def setup(bot):
    bot.add_cog(Streepje(bot))
