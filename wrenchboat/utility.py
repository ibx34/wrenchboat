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

    @commands.command(
        name="gibmeinfo",
        usage="@user",
        description="Get info on a user. (Don't add a user to get your own info).",
    )
    async def _userinfo(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author

        try:
            roles = [x.mention for x in user.roles]
            await ctx.channel.send(
                dedent(
                    f"""
            **User**: {user} ({user.id}) ({user.mention})
            **Create At**: {user.created_at.strftime('%m/%d/%Y')} ({arrow.get(user.created_at).humanize()})
            **Joined At**: {user.joined_at.strftime('%m/%d/%Y')} ({arrow.get(user.joined_at).humanize()})
            {f"**In voice**: #{user.voice.channel.name} ({user.voice.channel.id})" if user.voice else " "}
            **Roles**: {', '.join(roles[:40])}
            """
                ),
                allowed_mentions=discord.AllowedMentions(
                    everyone=False, roles=False, users=False
                ),
            )
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

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


def setup(bot):
    bot.add_cog(utility(bot))
