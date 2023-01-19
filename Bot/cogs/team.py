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
            if role.name.startswith("create-"):
                roles[role.name] = role
        return roles
    
    def getRoleAuthorReaction(self, reaction):
        for role in reaction.message.author.roles:
            if role.name.startswith("create-"):
                return role
        return None
    def getAuthorRoles(self, message):
        roles = []
        for role in message.author.roles:
            if role.name.startswith("create-"):
                return role
    def getMemberRoles(self, member):
        roles = []
        for role in member.roles:
            if role.name.startswith("create-"):
                roles.append(role)
        return roles

    @commands.Cog.listener()
    async def on_message(self, message):
        # check if the message starts with create-
        if message.channel.id == self.channel_id:
            if (message.content.startswith("create-") and len(message.mentions) > 0):
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
                        description="To find a team explore the <#950436316728946688> channel! Please use ```create-<TeamName> @member1 @member2``` to create a team.",
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
            if role.name == self.admin_role or role.name == "Owasp" or role.name == "Core 2nd Yr 😎":
                isMod = True
                break
            else:
                isMod = False
        
        # # make sure the user is authorised and channel is from the one and only channel
        # if user != self.bot.user and isMod == True and reaction.message.channel.id == self.channel_id:
        #     # check if user is in the db
        #     # author id of message
        if not isMod:
            return
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
        team_name = reaction.message.content.replace(" ", "").split("<")[0]
        print(team_name)
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
        bot_role = self.getRole("Owasp", reaction.message)
        admin_role = self.getRole(self.admin_role, reaction.message)
        print(admin_role)

        # create a category, vc, text channel where access is given to users with the team role and secretaries role
        category = await reaction.message.guild.create_category(team_name)
        await category.set_permissions(role, read_messages=True, send_messages=True, read_message_history=True)
        await category.set_permissions(admin_role, read_messages=True, send_messages=True, read_message_history=True)
        await category.set_permissions(bot_role, read_messages=True, send_messages=True, read_message_history=True)
        await category.set_permissions(reaction.message.guild.default_role, read_messages=False, send_messages=False, read_message_history=False)
        # create a text channel
        text_channel = await reaction.message.guild.create_text_channel(team_name, category=category)
        await text_channel.set_permissions(role, read_messages=True, send_messages=True, read_message_history=True)
        await text_channel.set_permissions(admin_role, read_messages=True, send_messages=True, read_message_history=True)
        await text_channel.set_permissions(bot_role, read_messages=True, send_messages=True, read_message_history=True)
        await text_channel.set_permissions(reaction.message.guild.default_role, read_messages=False, send_messages=False, read_message_history=False)
        # create a voice channel
        voice_channel = await reaction.message.guild.create_voice_channel(team_name, category=category)
        await voice_channel.set_permissions(role, read_messages=True, send_messages=True, read_message_history=True)
        await voice_channel.set_permissions(admin_role, read_messages=True, send_messages=True, read_message_history=True)
        await voice_channel.set_permissions(bot_role, read_messages=True, send_messages=True, read_message_history=True)
        await voice_channel.set_permissions(reaction.message.guild.default_role, read_messages=False, send_messages=False, read_message_history=False)
        
        # put vc and text channel in the category
        await text_channel.edit(category=category)
        await voice_channel.edit(category=category)
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
        # remove all roles with prefix "create-"
        roles_count = 0
        for role in ctx.guild.roles:
            print("role")
            if role.name.startswith("create-"):
                print(role.name)
                roles_count = roles_count + 1
                await role.delete()
        # remove all channels with prefix "create-"
        channels_count = 0
        for channel in ctx.guild.channels:
            if channel.name.startswith("create-"):
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
