from discord.ext import commands
import os
import discord
from database import SessionLocal
import models

admin_role = os.environ["ADMIN_ROLE_ID"]


class Team(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.role_name = os.environ['ROLE_NAME']

    @commands.hybrid_command(name="create", description="Create a team!", with_app_command=True)
    async def create(self, ctx: commands.Context, team_name: str, members: commands.Greedy[discord.Member]) -> None:
        team_name = team_name.lower()
        team_name = team_name.replace(" ", "-")
        print(
            f'Creating team {team_name} with members {[member.display_name for member in members]}')
        embed = discord.Embed(
            title='Creating Team',
            description=f'Team {team_name}',
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

        db = SessionLocal()

        # check if the team exists
        if db.query(models.Team).filter(models.Team.name == team_name).first():
            embed = discord.Embed(
                title='Error',
                description='Team already exists! Please use another name.',
                color=discord.Color.red()
            )
            print(f'Team {team_name} already exists!')
            await ctx.send(embed=embed)
            return

        # check if members are in a team
        for member in members:
            if db.query(models.Member).filter(models.Member.user_id == member.id).first():
                embed = discord.Embed(
                    title='Error',
                    description=f'{member.display_name} is already in a team!',
                    color=discord.Color.red()
                )
                print(f'{member.display_name} is already in a team')
                await ctx.send(embed=embed)
                return

        # create a role
        role = await ctx.guild.create_role(name=f'{self.role_name}-{team_name}')
        # add members to the role
        for member in members:
            await member.add_roles(role)

        # add team to the database
        team = models.Team(name=team_name)
        db.add(team)
        db.commit()

        # add members to the database
        for member in members:
            member = models.Member(user_id=member.id, team_id=team.id)
            db.add(member)
            db.commit()

        admin = ctx.guild.get_role(int(admin_role))

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            role: discord.PermissionOverwrite(read_messages=True),
            admin: discord.PermissionOverwrite(read_messages=True)
        }

        # create team category in the guild
        category = await ctx.guild.create_category(f'{self.role_name}-{team_name}')
        await category.edit(overwrites=overwrites)
        # create team text channel
        await ctx.guild.create_text_channel(f'{self.role_name}-{team_name}', category=category, overwrites=category.overwrites)
        # create team voice channel
        await ctx.guild.create_voice_channel(f'{self.role_name}-{team_name}', category=category, overwrites=category.overwrites)

        # send a message
        embed = discord.Embed(
            title="Team Created",
            description="Team {} created!".format(team_name),
            color=discord.Color.green()
        )
        print(f'Team {team_name} created!')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="remove", description="Remove a team", with_app_command=True)
    async def remove(self, ctx: commands.Context, team_name: str) -> None:
        team_name = team_name.lower()
        team_name = team_name.replace(" ", "-")

        if not ctx.author.get_role(int(admin_role)):
            embed = discord.Embed(
                title='Error',
                description='You do not have permission to use this command!',
                color=discord.Color.red()
            )
            print(f'{ctx.author.display_name} tried to reset teams')
            await ctx.send(embed=embed)
            return

        print(f'Removing team {team_name}')
        embed = discord.Embed(
            title='Removing Team',
            description=f'Team {team_name}',
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)

        db = SessionLocal()
        db.query(models.Member).filter(models.Member.team_id == db.query(
            models.Team).filter(models.Team.name == team_name).first().id).delete()
        db.query(models.Team).filter(models.Team.name == team_name).delete()
        db.commit()

        # remove role
        for role in ctx.guild.roles:
            if role.name == f'{self.role_name}-{team_name}':
                print(role.name)
                await role.delete()

        # remove channels
        for channel in ctx.guild.channels:
            if channel.name == f'{self.role_name}-{team_name}':
                print(channel.name)
                await channel.delete()

        embed = discord.Embed(
            title="Team Removed",
            description="Team {} removed!".format(team_name),
            color=discord.Color.green()
        )
        print(f'Team {team_name} removed!')
        await ctx.send(embed=embed)

    @commands.hybrid_command(name="reset", description="Reset all teams", with_app_command=True)
    async def reset(self, ctx: commands.Context) -> None:
        # check if author has role with id admin_role
        if not ctx.author.get_role(int(admin_role)):
            embed = discord.Embed(
                title='Error',
                description='You do not have permission to use this command!',
                color=discord.Color.red()
            )
            print(f'{ctx.author.display_name} tried to reset teams')
            await ctx.send(embed=embed)
            return

        db = SessionLocal()
        db.query(models.Member).delete()
        db.query(models.Team).delete()
        db.commit()

        embed = discord.Embed(
            title='Resetting Teams',
            description='Removing all teams',
            color=discord.Color.blue()
        )
        await ctx.send(embed=embed)
        print('Resetting teams')

        # get all team names from database
        team_names = []
        for team in db.query(models.Team).all():
            team_names.append(team.name)

        roles_count = 0
        # remove all roles
        for role in ctx.guild.roles:
            if role.name.startswith(self.role_name + '-') and role.name.split('-')[1] in team_names:
                print(role.name)
                await role.delete()
                roles_count += 1

        # remove all channels
        for channel in ctx.guild.channels:
            if channel.name.startswith(self.role_name + '-'):
                print(channel.name)
                await channel.delete()

        embed = discord.Embed(
            title="Success",
            description=f"{roles_count} team(s) deleted!",
            color=discord.Color.green()
        )
        await ctx.send(embed=embed)


async def setup(client) -> None:
    await client.add_cog(Team(client))
