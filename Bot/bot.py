import discord
from discord.ext import commands
import os
import models
from database import SessionLocal, engine

db = SessionLocal()
models.Base.metadata.create_all(bind=engine)

token = ''

prefix = "^"

bot = commands.Bot(command_prefix=prefix)

try:
    token = os.environ["TOKEN"]
except:
    print("Token not found")
    exit()

cogs = ["cogs.team"]

for cog in cogs:
    bot.load_extension(cog)

# command
@bot.command(command="channel")
async def channel(ctx):
    print(ctx.channel.id)
bot.run(token)
