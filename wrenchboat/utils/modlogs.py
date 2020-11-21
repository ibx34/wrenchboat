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
    "Mute": {  # Special Role Added
        "message": dedent(
            """
        **Mute** | Case {case}
        **User**: {user} ({user_id}) ({user_mention})
        **Role**: {role} ({role_id})
        **Reason**: {reason}
        **Moderator**: {moderator}
        """
        )
    },
    "Voicemute": {
        "message": dedent(
            """
        **Voicemute** | Case {case}
        **User**: {user} ({user_id}) ({user_mention})
        **Reason**: {reason}
        **Moderator**: {moderator}
        """
        )
    },
    "Voiceunmute": {
        "message": dedent(
            """
        **Voicemute** | Case {case}
        **User**: {user} ({user_id}) ({user_mention})
        **Reason**: {reason}
        **Moderator**: {moderator}
        """
        )
    },
    "Kick": {
        "message": dedent(
            """ 
        **Kick** | Case {case}
        **User**: {user} ({user_id}) ({user_mention})
        **Reason**: {reason}
        **Moderator**: {moderator}
        """
        )
    },
    "Ban": {
        "message": dedent(
            """ 
        **Ban** | Case {case}
        **User**: {user} ({user_id}) ({user_mention})
        **Reason**: {reason}
        **Moderator**: {moderator}
        """
        )
    },
    "Unban": {
        "message": dedent(
            """ 
        **Unban** | Case {case}
        **User**: {user} ({user_id}) ({user_mention})
        **Reason**: {reason}
        **Moderator**: {moderator}
        """
        )
    },
    "Unmute": {  # Special Role Removed
        "message": dedent(
            """
        **Unmute** | Case {case}
        **User**: {user} ({user_id}) ({user_mention})
        **Role**: {role} ({role_id})
        **Reason**: {reason}
        **Moderator**: {moderator}
        """
        )
    },
    "Warn": {
        "message": dedent(
            """ 
        **Warn** | Case {case}
        **User**: {user} ({user_id}) ({user_mention})
        **Reason**: {reason}
        **Moderator**: {moderator}
        """
        )
    },
    "Softban": {
        "message": dedent(
            """ 
        **Softban** | Case {case}
        **User**: {user} ({user_id}) ({user_mention})
        **Reason**: {reason}
        **Moderator**: {moderator}
        """
        )
    },
    "Forceban": {
        "message": dedent(
            """ 
        **Forceban** | Case {case}
        **User**: {user} ({user_id}) ({user_mention})
        **Reason**: {reason}
        **Moderator**: {moderator}
        """
        )
    },
}


class modlog_related:
    def __init__(
        self,
        user: discord.Member,
        moderator: discord.Member,
        reason: str,
        id: int,
        time,
        type: str,
        modlogs: int,
        pool,
        role: discord.Role = None,
    ):
        self.pool = pool
        self.user = user
        self.moderator = moderator
        self.reason = reason
        self.id = id
        self.time = time
        self.type = type
        self.modlogs = modlogs
        self.role = role

    async def insert(self):
        async with self.pool.acquire() as conn:
            try:
                await conn.execute(
                    "INSERT INTO infractions(target,moderator,reason,id,time_punsihed,type,modlogs) VALUES($1,$2,$3,$4,$5,$6,$7)",
                    self.user.id,
                    self.moderator.id,
                    self.reason,
                    self.id,
                    self.time,
                    self.type,
                    self.modlogs,
                )
            except Exception as err:
                print(err)
        return self


async def modlogs(
    self,
    moderator: discord.Member,
    user: discord.Member,
    reason: str,
    type: str,
    case: int,
    time,
    role: discord.Role = None,
):

    role = user.guild.default_role if role is None else role
    self.cases[user.guild.id] += 1
    if self.modlog_channel.get(user.guild.id):
        try:
            channel = self.get_channel(self.modlog_channel.get(user.guild.id))
            modlogs_message = await channel.send(
                modlogs_messages[type]["message"].format(
                    user=user,
                    user_id=user.id,
                    user_mention=user.mention,
                    reason=reason,
                    moderator=moderator,
                    case=self.cases[user.guild.id],
                    role_id=role.id,
                    role=role.name,
                )
            )
        except Exception as err:
            print(err)

    modlogs = modlog_related(
        pool=self.pool,
        user=user,
        moderator=moderator,
        type=type,
        id=self.cases[user.guild.id],
        time=time,
        role=role,
        modlogs=modlogs_message.id if modlogs_message is not None else None,
        reason=f"No reason provided. You can add a reason with `case {self.cases[user.guild.id]} <reason>`."
        if reason == config.default_reason
        else reason,
    )
    await modlogs.insert()
