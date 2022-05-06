import os
import discord
from discord.ext import commands
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth


class Spotify(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(client_id=self.client_id,
                                                            client_secret=self.client_secret,
                                                            redirect_uri="http://localhost",
                                                            scope="playlist-modify-public"))

    load_dotenv()
    song_requests = {}
    client_id = str(os.getenv('SPOTIFY_CLIENT_ID'))
    client_secret = str(os.getenv('SPOTIFY_CLIENT_SECRET'))
    spotify_role = discord.role
    playlist_id = '2nwGUMTtJUGp9dtSxPoiKZ'

    @discord.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if reaction.emoji == "👍":
            if reaction.message.id in self.song_requests.keys():
                if user.id == self.song_requests[reaction.message.id][1]:
                    await reaction.remove(user)
                if reaction.count == 4:
                    if reaction.message.id in self.song_requests.keys():
                        self.sp.playlist_add_items(self.playlist_id,
                                                   [self.song_requests[reaction.message.id][0]])
                        await reaction.message.channel.send("Added {Song} to the WTFP playlist".format(
                            Song=self.sp.track(self.song_requests[reaction.message.id][0])['name']))

    @discord.slash_command(name="addsong")
    async def add_song(self, ctx: discord.ApplicationContext, song):
        """Request to add a song to the WTFP Spotify playlist."""
        respond = await ctx.respond(
            "{Role} {Author} wants to add {Song} to the WTFP playlist \n4 👍 are needed!".format(
                Role=self.spotify_role.mention, Author=ctx.author.mention, Song=song))
        messages = await ctx.channel.history(limit=10).flatten()
        await messages[0].add_reaction(emoji='👍')
        self.song_requests[messages[0].id] = [song, ctx.author.id]

    @discord.slash_command(name="notifyspotify")
    async def notify_spotify(self, ctx):
        """Add yourself to the list to get notified when someone wants to add a song to the WTFP playlist"""
        await ctx.author.add_roles(self.spotify_role)
        await ctx.respond("Added " + ctx.author.name + " to the spotify notify list.")

    @discord.Cog.listener()
    async def on_ready(self):
        await self.bot.wait_until_ready()
        for server in self.bot.guilds:
            add_spotify_role = True

            for role in await server.fetch_roles():
                if role.name == 'Spotify':
                    self.spotify_role = role
                    add_spotify_role = False

            if add_spotify_role:
                self.spotify_role = await server.create_role(name="Spotify", colour=discord.Color.green())


def setup(bot):
    bot.add_cog(Spotify(bot))
