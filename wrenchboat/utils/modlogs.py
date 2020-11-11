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
import traceback

modlogs_messages = {
    "Mute": {
        "message": dedent("""
        **Special Role Added** | Case {case}
        **User**: {user} ({user_id}) ({user_mention})
        **Role**: {role} ({role_id})
        **Reason**: {reason}
        **Moderator**: {moderator}
        """)
    },
    "Kick": {
        "message": dedent(""" 
        **Kick** | Case {case}
        **User**: {user} ({user_id}) ({user_mention})
        **Reason**: {reason}
        **Moderator**: {moderator}
        """)
    },
    "Ban": {
        "message": dedent(""" 
        **Ban** | Case {case}
        **User**: {user} ({user_id}) ({user_mention})
        **Reason**: {reason}
        **Moderator**: {moderator}
        """)
    },
    "Unban": {
        "message": dedent(""" 
        **Unban** | Case {case}
        **User**: {user} ({user_id}) ({user_mention})
        **Reason**: {reason}
        **Moderator**: {moderator}
        """)
    },
    "Unmute": {
        "message": dedent("""
        **Special Role Removed** | Case {case}
        **User**: {user} ({user_id}) ({user_mention})
        **Role**: {role} ({role_id})
        **Reason**: {reason}
        **Moderator**: {moderator}
        """)
    },
    "Warn": {
        "message": dedent(""" 
        **Warn** | Case {case}
        **User**: {user} ({user_id}) ({user_mention})
        **Reason**: {reason}
        **Moderator**: {moderator}
        """)
    },
    "Softban": {
        "message": dedent(""" 
        **Softban** | Case {case}
        **User**: {user} ({user_id}) ({user_mention})
        **Reason**: {reason}
        **Moderator**: {moderator}
        """)
    },
    "Forceban": {
        "message": dedent(""" 
        **Forceban** | Case {case}
        **User**: {user} ({user_id}) ({user_mention})
        **Reason**: {reason}
        **Moderator**: {moderator}
        """)
    },
}


async def modlogs(self, moderator, user, reason, case, type, time, role=None):
    if role is None:
        role = user.guild.default_role

    async with self.pool.acquire() as conn:
        if self.modlog_channel.get(user.guild.id):

            modlogs = self.get_channel(self.modlog_channel.get(user.guild.id))
            self.cases[user.guild.id] += 1

            try:
                modlogs_message = await modlogs.send(
                    modlogs_messages[type]["message"].format(
                        **{
                            "user": user,
                            "user_id": user.id,
                            "user_mention": user.mention,
                            "reason": reason,
                            "moderator": moderator,
                            "case": self.cases[user.guild.id] ,
                            "role_id": role.id,
                            "role": role.name,
                        }
                    )
                )
                await conn.execute(
                    "INSERT INTO infractions(guild,type,moderator,target,time_punsihed,reason,modlogs,id) VALUES($1,$2,$3,$4,$5,$6,$7,$8)",
                    user.guild.id,
                    type,
                    moderator.id,
                    user.id,
                    time,
                    reason,
                    modlogs_message.id,
                    self.cases[user.guild.id] ,
                )
            except Exception as err:
                print(err)
                traceback.print_tb(err.__traceback__)