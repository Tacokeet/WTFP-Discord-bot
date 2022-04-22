import discord
from discord.ext import commands


class Jeopardy(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    teams = []
    buzer = False

    @commands.command(name="mkteam")
    async def make_team(self, ctx, personone, persontwo, teamname, soundid):
        """make team for Jeopardy."""
        if ctx.message.author.permissions_in(ctx.message.channel).ban_members:
            await ctx.send(
                "{personone} and {persontwo} are now team: {teamname} with soundID: {soundid}.".format(
                    personone=ctx.message.mentions[0].name,
                    persontwo=ctx.message.mentions[1].name, teamname=str(teamname), soundid=str(soundid)))
            self.teams.append([ctx.message.mentions[0].id, ctx.message.mentions[1].id, teamname, soundid])
        else:
            await ctx.send("Only admins are allowed to create teams.")

    @commands.command(name="reset")
    async def reset_question(self, ctx):
        """Reset question for Jeopardy."""
        if ctx.message.author.permissions_in(ctx.message.channel).ban_members:
            self.buzer = False
            await ctx.send("Buzzers are reset!")
        else:
            await ctx.send("Only admins are allowed to reset the question teams.")

    @commands.command(name="clrteams")
    async def clear_team(self, ctx):
        """clears teams for Jeopardy."""
        await ctx.send("Cleared all Jeopardy teams.")
        self.teams.clear()

    @commands.command(name="listteams")
    async def list_team(self, ctx):
        """lists all the teams for Jeopardy."""
        allteams = ""
        if allteams:
            for team in self.teams:
                allteams += "Team : " + team[2] + " with members: " + self.bot.get_user(
                    team[0]).name + " and " + self.bot.get_user(
                    team[1]).name + " with buzzer sound: " + team[3] + '\n'
            await ctx.send(allteams)
        else:
            await ctx.send("There aren't any teams, please make some teams.")

    @commands.command(name="buz")
    async def call(self, ctx):
        """Buzzez in for Jeopardy."""

        if self.teams:
            if self.buzer:
                await ctx.send("Buzzers are disabled waiting for reset!")
                return
            for team in self.teams:
                if ctx.message.author.id in team:
                    await ctx.send(team[2] + " Buzzed in!")
                    self.buzer = True
                    await Soundboard.soundboard(Soundboard(self.bot), ctx=ctx, sound=team[3])
                    return
            await ctx.send(
                ctx.message.author.name + " is not in a team!")
            return
        else:
            await ctx.send("There aren't any teams, please make some teams.")

    @call.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.channel.id is not ctx.author.voice.channel.id:
            if not ctx.author.voice:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
            if ctx.voice_client.is_playing():
                await ctx.send("Jeopardy is happening in another voice channel!")
                raise commands.CommandError("Author not in same voice channel.")
            else:
                await ctx.voice_client.disconnect()
                await ctx.author.voice.channel.connect()


def setup(bot):
    bot.add_cog(Jeopardy(bot))
