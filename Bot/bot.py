import discord
from discord.ext import commands
from database import SessionLocal, engine
import models
import os

token = ''


class TeamCreator(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.messages = True

        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents
        )

    async def setup_hook(self) -> None:
        extensions = [
            "cogs.team",
        ]

        for cog in extensions:
            await self.load_extension(cog)

        await self.tree.sync()
        commands = await self.tree.fetch_commands()
        [print(command.name) for command in commands]

    async def on_ready(self) -> None:
        print('Logged in as', self.user)

    async def on_command_error(self, ctx, error):
        embed = discord.Embed(
            title='Error',
            description=f'{error}',
            color=discord.Color.red()
        )
        await ctx.send(embed=embed)
        print(error)


try:
    token = os.environ["TOKEN"]
except:
    print("Token not found")
    exit()

if __name__ == '__main__':
    db = SessionLocal()
    models.Base.metadata.create_all(bind=engine)

    print("Running!")
    bot = TeamCreator()
    bot.run(token)
