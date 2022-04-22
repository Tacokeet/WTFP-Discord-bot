import discord
from discord.ext import commands
from discordTogether import DiscordTogether
from discord.commands import Option


class Together(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.togetherControl = DiscordTogether(bot)

    async def get_options(self, ctx: discord.AutocompleteContext):
        return [opt for opt in ['youtube', 'poker', 'chess', 'betrayal', 'fishing'] if ctx.value in opt]

    @discord.slash_command(name='together')
    async def together(self, ctx: discord.ApplicationContext,
                       option: Option(str, "Pick a sound!", autocomplete=get_options)):
        """Together: youtube, poker, chess, betrayal, fishing"""
        link = await self.togetherControl.create_link(ctx.author.voice.channel.id, str(option))
        await ctx.send(f"Click the blue link!\n{link}")

    @together.before_invoke
    async def ensure_voice(self, ctx):
        if ctx.voice_client is None:
            if ctx.author.voice:
                await ctx.author.voice.channel.connect()
            else:
                await ctx.send("You are not connected to a voice channel.")
                raise commands.CommandError("Author not connected to a voice channel.")
        elif ctx.voice_client.is_playing():
            ctx.voice_client.stop()


def setup(bot):
    bot.add_cog(Together(bot))
