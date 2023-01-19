import discord
from discord.ext import commands
import os
import models
from database import SessionLocal, engine

db = SessionLocal()
models.Base.metadata.create_all(bind=engine)

token = ''

prefix = ")"

bot = commands.Bot(command_prefix=prefix)

try:
    token = os.environ["TOKEN"]
except:
    print("Token not found")
    exit()

cogs = ["cogs.team"]

for cog in cogs:
    bot.load_extension(cog)

# create a command
@bot.command()
async def ping(ctx):
    await ctx.send(f"Pong! {round(bot.latency * 1000)}ms")
if __name__ == '__main__':
    try:
        print("Running!")
        bot.run(token)
    except:
        print('Invalid Token')
        exit(1)
