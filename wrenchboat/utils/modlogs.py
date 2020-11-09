import asyncio
import os
import random
import sys
from textwrap import dedent

import aiohttp
import aioredis
import asyncpg
import config
import discord
from discord.ext import commands

async def modlogs(self,moderator,user,reason,case,type,time,role=None):
    async with self.pool.acquire() as conn:
        guild = await conn.fetchrow("SELECT * FROM guilds WHERE id = $1",user.guild.id)
        if guild['modlogs']:
            modlogs = self.get_channel(guild['modlogs'])

            modlogs_message = await modlogs.send("The wizard couldn't find this modlog.")
            try:
                data = await conn.fetchrow("INSERT INTO infractions(guild,type,moderator,target,time_punsihed,reason,modlogs) VALUES($1,$2,$3,$4,$5,$6,$7) RETURNING *",user.guild.id,type,moderator.id,user.id,time,reason,modlogs_message.id)
                await modlogs_message.edit(content=dedent(f"""
                **{type}** | Case {data['id']}
                **User**: {user} ({user.id}) ({user.mention})
                **Reason**: {reason}
                **Responsible Moderator**: {moderator}
                {f"**Role**: {role.name} ({role.id})" if role is not None else ""}
                """))
            except Exception as err:
                await modlogs_message.edit(content=f"There was an error while doing something :/\n{err}")