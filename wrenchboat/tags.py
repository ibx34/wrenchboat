"""
Copyright 2020 ibx34

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

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

from wrenchboat.utils import pagination

class tags(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.group(name="tag",usage="<name>",description="View a tag's content.",invoke_without_command=True)
    async def _tag(self,ctx,*,name):
        async with self.bot.pool.acquire() as conn:
            tag = await conn.fetchrow("SELECT * FROM tags WHERE name = $1 AND guild = $2",name.lower(),ctx.channel.guild.id)

            if not tag:
                return await ctx.channel.send("That isn't a tag. Don't know what you're thinking of.")           

            try:
                await ctx.channel.send(tag['content'],
                    allowed_mentions=discord.AllowedMentions(
                        everyone=False, roles=False
                    ),
                )
                await conn.execute("UPDATE tags SET uses = uses + $1 WHERE id = $2 AND guild = $3",1, tag['id'], tag['guild'])
            except Exception as err:
                return await ctx.channel.send(f"Don't expect me to know what happened >:)\n{err}")
                
    @_tag.command(name="create",usage="(name) (content)",description="Create a tag for all users to see!!!")
    async def _tag_create(self,ctx,name,*,content):
        if len(name) > 30:
            return await ctx.channel.send("Nope. Not gonna do it. No, no no. (Name too long)")  
        if len(content) > 2000:
            return await ctx.channel.send("Nope. Not gonna do it. No, no no. (Content too long)")  

        async with self.bot.pool.acquire() as conn:
            tag = await conn.fetchrow("SELECT * FROM tags WHERE name = $1 AND guild = $2",name,ctx.channel.guild.id)

            if tag:
                return await ctx.channel.send("No go my guy... That tag already exists!")   
            
            try:
                await conn.fetchrow(f"INSERT INTO tags(created,name,content,guild,author) VALUES($1,$2,$3,$4,$5) RETURNING *",datetime.utcnow(),name.lower(),content,ctx.channel.guild.id,ctx.author.id)
            except Exception as err:
                return await ctx.channel.send(f"Don't expect me to know what happened >:)\n{err}")

            await ctx.channel.send(f":ok_hand: created a tag with the name {name}")
        
    @_tag.command(name="delete",usage="(tag)",description="Delete a tag on the server. You must be the tag owner, or have manage servers to do this.")
    async def _tag_delete(self,ctx,*,name):
        async with self.bot.pool.acquire() as conn:
            tag = await conn.fetchrow("SELECT * FROM tags WHERE name = $1 AND guild = $2",name,ctx.channel.guild.id)

            if not tag:
                return await ctx.channel.send("That isn't a tag. Don't know what you're thinking of.")       

            perms = ctx.channel.permissions_for(ctx.author)
            if ctx.author.id != tag['author']:
                if perms.manage_guild or perms.administrator:
                    pass
                else:
                    return

            try:
                await conn.fetchrow("DELETE FROM tags WHERE id = $1 AND guild = $2",tag['id'],ctx.channel.guild.id)
            except Exception as err:
                return await ctx.channel.send(f"Don't expect me to know what happened >:)\n{err}")
            
            await ctx.channel.send(f":ok_hand: I deleted a tag with the name {tag['name']}")
    
    @_tag.command(name="stats",usage="(tag)",description="Get some general stats on a tag")
    async def _tag_stats(self,ctx,*,name):
        async with self.bot.pool.acquire() as conn:
            tag = await conn.fetchrow("SELECT * FROM tags WHERE name = $1 AND guild = $2",name,ctx.channel.guild.id)

            if not tag:
                return await ctx.channel.send("That isn't a tag. Don't know what you're thinking of.")       

            embed = discord.Embed(color=0x99AAB5,description=f"**Response**:\n{tag['content']}")
            embed.set_author(name=tag['name'])
            embed.add_field(name="Author",value=f"<@{tag['author']}>")
            embed.add_field(name="Uses",value=f"{tag['uses']}")
            embed.add_field(name="Created",value=f"{arrow.get(tag['created']).humanize()} ({tag['created']})",inline=False)
            try:
                await ctx.channel.send(embed=embed)
            except Exception as err:
                return await ctx.channel.send(f"Something went wrong :thonk: (A different message from always huh)\n{err}")


def setup(bot):
    bot.add_cog(tags(bot))
