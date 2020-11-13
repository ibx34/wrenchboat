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
    
    @commands.command(name="sql", usage="query", description="Execute some cute sql in Discord **WWOWOWOWOWO**")
    @commands.is_owner()
    async def _sql(self,ctx,*,statement):
        async with self.bot.pool.acquire() as conn:
            try:
                await conn.fetchrow(statement)
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )
            
            await ctx.channel.send(":ok_hand:")

    @commands.command(name="bug", usage="None", description="Found a bug? Report it at the link provided.")
    async def _bug(self,ctx):

        return await ctx.channel.send("You can report a bug here: --> <https://rb.gy/h2kktv>! Thank you in advance")
    
    @commands.command(name="support",usage="None",description="Need help? Join our support server and we will try our best")
    async def _support(self,ctx):

        return await ctx.channel.send(f"You can join our support server @: {config.support}")

    """
    highligher
    """

    @commands.group(name="highlight",description="Highlight words and get dmed when someone mentions it!",invoke_without_command=True,aliases=['hl'])
    async def _highlight(self,ctx):
        return
    
    @_highlight.command(name="add",usage="(word or phrase)",description="Add a word or phrase to your highligh list.")
    async def _add(self,ctx,*,word:str):

        if len(word) > 2000:
            return await ctx.channel.send("Nope. Not gonna do it. No, no no. (Word or prhase too long)") 

        async with self.bot.pool.acquire() as conn:
            highlight = await conn.fetchrow("SELECT * FROM highlights WHERE author = $1 AND guild = $2 AND phrase = $3",ctx.author.id,ctx.channel.guild.id,word.lower())

            if highlight:
                return await ctx.channel.send("No go!!!!! That word is already highlighted")   
            
            try:
                i = await conn.fetchrow(f"INSERT INTO highlights(author,guild,phrase) VALUES($1,$2,$3) RETURNING *",ctx.author.id,ctx.channel.guild.id,word.lower())
                self.bot.highlights[i['id']] = {"phrase": i['phrase'], "author": i['author'], "guild": i['guild']}
            except Exception as err:
                return await ctx.channel.send(f"Don't expect me to know what happened >:)\n{err}")

            await ctx.channel.send(f":ok_hand:") 

    @_highlight.command(name="delete",usage="(word or phrase)",description="Delete a previously highlighted word or phrase")
    async def _delete(self,ctx,*,word:str):
        async with self.bot.pool.acquire() as conn:
            highlight = await conn.fetchrow("SELECT * FROM highlights WHERE author = $1 AND guild = $2 AND phrase = $3",ctx.author.id,ctx.channel.guild.id,word.lower())

            if not highlight:
                return await ctx.channel.send("Couldn't that highlighted phrase or word... ")   
            
            try:
                i = await conn.fetchrow(f"DELETE FROM highlights WHERE author = $1 AND guild = $2 AND phrase = $3",ctx.author.id,ctx.channel.guild.id,word.lower())
                del self.bot.highlights[highlight['id']]
            except Exception as err:
                return await ctx.channel.send(f"Don't expect me to know what happened >:)\n{err}")

            await ctx.channel.send(f":ok_hand: (deleted ig)") 

    @_highlight.command(name="clear",description="Delete all your highlighted words for the server.")
    async def _clear(self,ctx):
        async with self.bot.pool.acquire() as conn:
            try:
                await conn.fetchrow(f"DELETE FROM highlights WHERE author = $1 AND guild = $2",ctx.author.id,ctx.channel.guild.id)
                for x in sorted(self.bot.highlights):
                    if self.bot.highlights[x]['author'] == ctx.author.id and self.bot.highlights[x]['guild'] == ctx.guild.id:
                        del self.bot.highlights[x]
            except Exception as err:
                return await ctx.channel.send(f"Don't expect me to know what happened >:)\n{err}")

            await ctx.channel.send(f":ok_hand: I deleted all your highlighted words!!!") 

def setup(bot):
    bot.add_cog(utility(bot))
