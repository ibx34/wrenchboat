import csv
import os
import random
import re
import sys
from datetime import datetime
from textwrap import dedent

import aiohttp
import aioredis
import arrow
import asyncpg
import config
import discord
from discord.ext import commands

from wrenchboat.utils.modlogs import modlogs


class utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="gibmeinfo",usage="@user",description="Get info on a user. (Don't add a user to get your own info).",)
    async def _userinfo(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author

        embed = discord.Embed(color=0x99AAB5)
        embed.set_author(name=user,icon_url=user.avatar_url)
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(name="User Information", value=f"Id: {user.id}\nProfile: {user.mention}\nCreated: {arrow.get(user.created_at).humanize()} ({user.created_at})",inline=False)
        embed.add_field(name="Member Information", value=f"Joined: {arrow.get(user.joined_at).humanize()} ({user.joined_at})",inline=False)
        embed.add_field(name="Infractions", value=f"Total Infractions: {await self.bot.pool.fetchval('SELECT COUNT(*) FROM infractions WHERE guild = $1 AND target = $2',ctx.channel.guild.id,user.id)}\nUnique Servers: {await self.bot.pool.fetchval('SELECT COUNT(DISTINCT guild) FROM infractions WHERE target = $1',user.id)}")

        try:    
            await ctx.channel.send(embed=embed)
        except Exception as err:
            return await ctx.channel.send(f"Don't expect me to know what happened >:)\n{err}")

    @commands.command(name="serverinfo",usage="None",description="Get info on your current server.")
    async def _serverinfo(self,ctx):

        embed = discord.Embed(color=0x99AAB5)
        embed.set_author(name=ctx.guild.name,icon_url=ctx.guild.icon_url)
        embed.set_thumbnail(url=ctx.guild.icon_url)        
        embed.add_field(name="Server Information",value=f"Id: {ctx.channel.guild.id}\nMembers: {ctx.channel.guild.member_count:,d}\nCreated: {arrow.get(ctx.channel.guild.created_at).humanize()} ({ctx.channel.guild.created_at})",inline=False)
        embed.add_field(name="Owner Information",value=f"Id: {ctx.channel.guild.owner.id}\nProfile: {ctx.channel.guild.owner.mention}\nCreated: {arrow.get(ctx.channel.guild.owner.created_at).humanize()} ({ctx.channel.guild.owner.created_at})",inline=False)
        embed.add_field(name="Infractions",value=f"Total Infractions: {await self.bot.pool.fetchval('SELECT COUNT(*) FROM infractions WHERE guild = $1',ctx.channel.guild.id)}",inline=False)
        
        try:    
            await ctx.channel.send(embed=embed)
        except Exception as err:
            return await ctx.channel.send(f"Don't expect me to know what happened >:)\n{err}")


    @commands.command(
        name="avy",
        usage="@user",
        description="Get a user's avatar (Don't add a user to get your own avatar)",
    )
    async def _avy(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author

        try:
            embed = discord.Embed(color=0x99AAB5)
            embed.set_image(url=user.avatar_url)
            await ctx.channel.send(embed=embed)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )
    
    @commands.command(name="bug", usage="None", description="Found a bug? Report it at the link provided.")
    async def _bug(self,ctx):

        return await ctx.channel.send("You can report a bug here: --> <https://rb.gy/h2kktv>! Thank you in advance")
    
    @commands.command(name="support",usage="None",description="Need help? Join our support server and we will try our best")
    async def _support(self,ctx):

        return await ctx.channel.send(f"You can join our support server @: {config.support}")

def setup(bot):
    bot.add_cog(utility(bot))
