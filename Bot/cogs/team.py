from sqlalchemy import true
from discord.ext import commands
import os
import discord
from discord.utils import get
from database import SessionLocal, engine
import models

channel_id = os.environ["CHANNEL"]
admin_role_name = os.environ["ADMIN_ROLE"]
class Team(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = int(channel_id)
        self.admin_role = admin_role_name
    
    def getRole(self, role_name, message):
        for role in message.guild.roles:
            if role.name == role_name:
                return role
        return None

    def getRoles(self, message):
        roles = {}
        for role in message.guild.roles:
            if role.name.startswith("dv-"):
                roles[role.name] = role
        return roles
    
    def getRoleAuthorReaction(self, reaction):
        for role in reaction.message.author.roles:
            if role.name.startswith("dv-"):
                return role
        return None
    def getAuthorRoles(self, message):
        roles = []
        for role in message.author.roles:
            if role.name.startswith("dv-"):
                return role
    def getMemberRoles(self, member):
        roles = []
        for role in member.roles:
            if role.name.startswith("dv-"):
                roles.append(role)
        return roles

    @commands.Cog.listener()
    async def on_message(self, message):
        # check if the message starts with dv-
        if message.channel.id == self.channel_id:
            if (message.content.startswith("dv-") and len(message.mentions) > 0):
                # team name
                print("here")
                team_name = message.content.split(" ")[0].replace(" ", "")
                # get all roles
                teams = self.getRoles(message)
                if team_name in teams:
                    # embed
                    embed = discord.Embed(
                        title="Error",
                        description="Team already exists!",
                        color=0xFF0000
                    )
                    await message.reply(embed=embed)
                    return
                # check if any mentions are already in a team
                for member in message.mentions:
                    if self.getMemberRoles(member):
                        # embed
                        embed = discord.Embed(
                            title="Error",
                            description="{} is already in a team!".format(member.display_name),
                            color=0xFF0000
                        )
                        await message.reply(embed=embed)
                        return
                # check if the author has a team
                if self.getAuthorRoles(message):
                    # embed
                    embed = discord.Embed(
                        title="Error",
                        description="You are already in a team!",
                        color=0xFF0000
                    )
                    await message.reply(embed=embed)
                    return
                # create a reaction button on the message
                await message.add_reaction("\U0001F44D")
            else:
                # check if message is reaction
                if message.author.id == self.bot.user.id:
                    return
                else:
                    # message delete
                    await message.delete()
                    # embed
                    # 950436316728946688 mention this channel
                    embed = discord.Embed(
                        title="Spam Error",
                        description="To find a team explore the <#950436316728946688> channel! Please use ```dv-<TeamName> @member1 @member2``` to create a team.",
                        color=0xFF0000
                    )
                    await message.channel.send(embed=embed)

    

    # when a reaction is clicked
    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        db = SessionLocal()
        # print the message if the reaction added is not the bot
        # check if user is a Moderator
        isMod = False

        # get roles of the user
        for role in user.roles:
            if role.name == self.admin_role or role.name == "Core 😎" or role.name == "Core 2nd Yr 😎":
                isMod = True
                break
            else:
                isMod = False
        
        # make sure the user is authorised and channel is from the one and only channel
        if user != self.bot.user and isMod == True and reaction.message.channel.id == self.channel_id:
            # check if user is in the db
            # author id of message
            if db.query(models.Member).filter(models.Member.user_id == reaction.message.author.id).first():
                # already in a team 
                embed = discord.Embed(
                    title="Error",
                    description="You are already in a team!",
                    color=0xFF0000
                )
                await reaction.message.reply(embed=embed)
                return
            for member in reaction.message.mentions:
                # check member id in the database
                if db.query(models.Member).filter(models.Member.user_id == member.id).first():
                    # already in a team 
                    embed = discord.Embed(
                        title="Error",
                        description="{} is already in a team!".format(member.display_name),
                        color=0xFF0000
                    )
                    await reaction.message.reply(embed=embed)
                    return
            
            # get the team role
            team_name = reaction.message.content.split(" ")[0].replace(" ", "")
            # get the author of the message
            author = reaction.message.author
            # create a role
            role = await reaction.message.guild.create_role(name=team_name)
            # add the role to the author
            await author.add_roles(role)
            # add the role to the mentions
            for member in reaction.message.mentions:
                await member.add_roles(role)
            
            # create a category, vc, text channel
            bot_role = self.getRole("TeamCreatorBot", reaction.message)
            admin_role = self.getRole(self.admin_role, reaction.message)
            print(admin_role)

            overwrites = {}

            # if admin_role is not None and bot_role is not None:
            #     overwrites = {
            #         role: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
            #         admin_role: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True, manage_roles=True),
            #         bot_role: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_channels=True, manage_roles=True),
            #         reaction.message.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False)
            #     }
            # else:
            overwrites = {
                reaction.message.guild.default_role: discord.PermissionOverwrite(read_messages=False, send_messages=False),
                role: discord.PermissionOverwrite(read_messages=True, send_messages=True, read_message_history=True),
                bot_role: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_guild=True),
                admin_role: discord.PermissionOverwrite(read_messages=True, send_messages=True, manage_guild=True)
            }
            
            # create a category
            category = await reaction.message.guild.create_category_channel(name=team_name, overwrites=overwrites)
            # create a voice channel
            vc = await reaction.message.guild.create_voice_channel(name=team_name, overwrites=overwrites)
            # create a text channel
            text = await reaction.message.guild.create_text_channel(name=team_name, overwrites=overwrites)

            await text.edit(category=category)
            await vc.edit(category=category)

            # create team 
            # check if team is in the database
            team = db.query(models.Team).filter(models.Team.name == team_name).first()
            if not team:
                team = models.Team(
                    name=team_name,
                )
                db.add(team)
                db.commit()
            # create member
            member = models.Member(
                user_id=author.id,
                team_id=team.id
            )
            db.add(member)
            db.commit()
            # create member
            for member in reaction.message.mentions:
                member = models.Member(
                    user_id=member.id,
                    team_id=team.id
                )
                db.add(member)
                db.commit()
            # create a reaction button on the message
            await reaction.message.add_reaction("\U0001F44D")
            # embed
            embed = discord.Embed(
                title="Success",
                description="Team created!",
                color=0x00FF00
            )
            await reaction.message.reply(embed=embed)

    @commands.command(name="reset", aliases=["r"])
    async def reset(self, ctx):
        # get author id
        author_id = ctx.author.id
        # author authorised
        if author_id == int(os.environ["ADMIN_ID"]):
            # remove all roles with prefix "dv-"
            roles_count = 0
            for role in ctx.guild.roles:
                print("role")
                if role.name.startswith("dv-"):
                    print(role.name)
                    roles_count = roles_count + 1
                    await role.delete()
            # remove all channels with prefix "dv-"
            channels_count = 0
            for channel in ctx.guild.channels:
                if channel.name.startswith("dv-"):
                    print(channel.name)
                    channels_count = channels_count + 1
                    await channel.delete()
            # embed 
            embed = discord.Embed(
                title="Success",
                description=f"{roles_count} team(s) deleted!",
                color=0x00FF00
            )
            await ctx.send(embed=embed)
def setup(client):
    client.add_cog(Team(client))
