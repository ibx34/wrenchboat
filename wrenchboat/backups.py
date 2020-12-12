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

class backups(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="backup",usage="(user)",description="Save a user's current roles and apply them later.",invoke_without_command=True)
    @commands.has_permissions(manage_roles=True)
    async def _backup(self,ctx,user:discord.Member):
        async with self.bot.pool.acquire() as conn:
            try_and_upate = await conn.fetchrow("SELECT * FROM user_backups WHERE target = $1 AND guild = $2",user.id,ctx.channel.guild.id)

            if try_and_upate:
                try:
                    await conn.fetchrow("UPDATE user_backups SET roles = $1 WHERE target = $2 AND guild = $3 AND id = $4 RETURNING *",[x.id for x in user.roles],user.id,ctx.channel.guild.id,try_and_upate['id'])
                    return await ctx.channel.send("HEY!!!! I needa tell you smth. The user already had a backup so I went ahead an updated that one!")
                except:
                    return

            try:
                await conn.fetchrow("INSERT INTO user_backups(roles,target,guild) VALUES($1,$2,$3) RETURNING *",[x.id for x in user.roles],user.id,ctx.channel.guild.id)
                return await ctx.channel.send(f"Epic,,, {user}'s roles are now backuped! (If that is a word, idk)")
            except Exception as err:
                print(err)

    @_backup.command(name="restore",usage="(user)",description="Will attempt to add their roles from a previous backup.")
    @commands.has_permissions(manage_roles=True)
    async def _backup_restore(self,ctx,user:discord.Member):
       async with self.bot.pool.acquire() as conn:
            try_and_restore = await conn.fetchrow("SELECT * FROM user_backups WHERE target = $1 AND guild = $2",user.id,ctx.channel.guild.id)
            
            if not try_and_restore:
                return await ctx.channel.send(f":rotating_light: They don't have a backup... You can create run one by running `{ctx.prefix}backup {user.id}`!!!!!!!!!!")
            
            try:
                for x in try_and_restore['roles']:
                    try:
                        role = ctx.channel.guild.get_role(x)
                        await user.add_roles(role)
                    except:
                        continue

                return await ctx.channel.send("**Phew**!!! That was close, don't worry I restored the roles I could :)")
            except Exception as err:
                print(err)

    @_backup.command(name="delete",usage="(user)",description="Delete a previous backup on a user, this **can't** be undone.")
    @commands.has_permissions(manage_roles=True)
    async def _backup_delete(self,ctx,user:discord.Member):
       async with self.bot.pool.acquire() as conn:
            try_and_remove = await conn.fetchrow("SELECT * FROM user_backups WHERE target = $1 AND guild = $2",user.id,ctx.channel.guild.id)
            
            if not try_and_remove:
                return await ctx.channel.send(f":rotating_light: They don't have a backup... You can create run one by running `{ctx.prefix}backup {user.id}`!!!!!!!!!!")

            try:
                await conn.execute("DELETE FROM user_backups WHERE id = $1",try_and_remove['id'])
                return await ctx.channel.send("Deleted the backup! They're not longer insured.")
            except Exception as err:
                print(err)

    @_backup.command(name="update",usage="(user)",description="Update a user's backup.")
    @commands.has_permissions(manage_roles=True)
    async def _backup_update(self,ctx,user:discord.Member):
       async with self.bot.pool.acquire() as conn:
            try_and_update = await conn.fetchrow("SELECT * FROM user_backups WHERE target = $1 AND guild = $2",user.id,ctx.channel.guild.id)
            
            if not try_and_update:
                return await ctx.channel.send(f":rotating_light: They don't have a backup... You can create run one by running `{ctx.prefix}backup {user.id}`!!!!!!!!!!")

            try:
                await conn.execute("UPDATE user_backups SET roles = $1 WHERE id = $2",[x.id for x in user.roles],try_and_update['id'])
                return await ctx.channel.send(f"Updated the backup! The following roles are now on it: {','.join([f'<@&{x.id}>' for x in user.roles])}",
                allowed_mentions=discord.AllowedMentions(
                    everyone=False, roles=False, users=False
                ),)
            except Exception as err:
                print(err)
def setup(bot):
    bot.add_cog(backups(bot))