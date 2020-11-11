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
from wrenchboat.utils.checks import checks
from wrenchboat.utils.modlogs import modlogs


class config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="modlogs",
        usage="<#channel>",
        description="Sets your server's modlogs. The decancer command will also be logged here.",
    )
    @commands.has_permissions(administrator=True)
    async def _modlogs(self, ctx, *, channel: discord.TextChannel = None):
        # if channel is None:
        #     channel = ctx.channel

        async with self.bot.pool.acquire() as conn:
            try:
                await conn.execute(
                    "UPDATE guilds SET modlogs = $1 WHERE id = $2",
                    None if channel is None else channel.id,
                    ctx.channel.guild.id,
                )
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(
                f"""OMG THAT TOOK EFFORT!!!! I set your modlogs to {channel.mention if channel is not None else "Disabled"}."""
            )

    @commands.command(
        name="muterole",
        usage="@role",
        description="Set your server's mute role. No the bot wont make one for you, don't be lazy.",
    )
    @commands.has_permissions(administrator=True)
    async def _muterole(self, ctx, *, role: discord.Role = None):
        async with self.bot.pool.acquire() as conn:
            try:
                await conn.execute(
                    "UPDATE guilds SET muterole = $1 WHERE id = $2",
                    None if role is None else role.id,
                    ctx.channel.guild.id,
                )
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(
                f"""**You ask too much of me!** I have set your mute role to {role.mention if role is not None else "Disabled"}""",
                allowed_mentions=discord.AllowedMentions(
                    everyone=False, roles=False, users=False
                ),
            )

    @commands.command(
        name="dontmuterole",
        usage="@role",
        description="Set your server's \"don't mute role\". This will make people with it un-muteable (Idea from discord bots).",
    )
    @commands.has_permissions(administrator=True)
    async def _dontmuterole(self, ctx, *, role: discord.Role = None):
        async with self.bot.pool.acquire() as conn:
            try:
                await conn.execute(
                    "UPDATE guilds SET dontmute = $1 WHERE id = $2",
                    None if role is None else role.id,
                    ctx.channel.guild.id,
                )
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(
                f"""Don't expect some edgy response from me... I have set your \"don't mute role\" to {role.mention  if role is not None else "Disabled"}""",
                allowed_mentions=discord.AllowedMentions(
                    everyone=False, roles=False, users=False
                ),
            )

    @commands.command(
        name="antihoist",
        description="Stop users from hoisting by removing the special character and replacing it with a *very* nice name.",
    )
    @commands.has_permissions(administrator=True)
    async def _antihoist(self, ctx):
        async with self.bot.pool.acquire() as conn:

            try:
                update = await conn.fetchrow(
                    "UPDATE guilds SET antihoist = $1 WHERE id = $2 RETURNING *",
                    False if self.bot.antihoist[ctx.channel.guild.id] else True,
                    ctx.channel.guild.id,
                )
                self.bot.antihoist[ctx.channel.guild.id] = update["antihoist"]
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send("👌")

    @commands.group(
        name="antiprofainity",
        usage="<BAN, KICK, MUTE, DELETE>",
        description="Enable antiprofainity on your server. When enabled the bot will do the predefined action when a user curses (:warning: THIS CAN BE HARSH)",
        invoke_without_command=True,
    )
    @commands.has_permissions(administrator=True)
    async def _antiprofainity(self, ctx, *, option):

        if option.lower() not in ["ban", "mute", "kick", "delete"]:
            return await ctx.channel.send(
                "**BRUH** provide an actual action my guy... (Actions: warn, kick, mute)"
            )

        async with self.bot.pool.acquire() as conn:

            try:
                await conn.execute(
                    "UPDATE guilds SET antiprofanity = $1 WHERE id = $2",
                    option.lower(),
                    ctx.channel.guild.id,
                )
                self.bot.automod[ctx.channel.guild.id] = option.lower()
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(
                f"Cool. I set your server's antiprofanity to {option.lower()}"
            )

    @_antiprofainity.command(
        name="disable", description="Disable antiprofanity for your server."
    )
    @commands.has_permissions(administrator=True)
    async def _antiprofainity_disable(self, ctx):

        async with self.bot.pool.acquire() as conn:

            try:
                await conn.execute(
                    "UPDATE guilds SET antiprofanity = $1 AND id = $2",
                    None,
                    ctx.channel.guild.id,
                )
                del self.bot.automod[ctx.channel.guild.id]
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(f"👍")

    @commands.command(name="modrole",description="Set your server's modrole. This is used for the `pingmod` command")
    @commands.has_permissions(administrator=True)
    async def _modrole(self, ctx,role:discord.Role = None):
        async with self.bot.pool.acquire() as conn:
            try:
                await conn.execute(
                    "UPDATE guilds SET modrole = $1 WHERE id = $2",
                    None if role is None else role.id,
                    ctx.channel.guild.id,
                )
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(
                f"""**You ask too much of me!** I have set your mod role to {role.mention if role is not None else "Disabled"}""",
                allowed_mentions=discord.AllowedMentions(
                    everyone=False, roles=False, users=False
                ),
            )

    @commands.command(name="pingmod",description="Ping a random **online** moderator from your server's mod role (Inspired by Kitchen Sink)")
    async def _pingmod(self,ctx,*,message):

        embed = discord.Embed(color=0x99AAB5,description=message,timestmap=datetime.utcnow())
        embed.set_footer(text=f"{ctx.author} | {ctx.author.id}",icon_url=ctx.author.avatar_url)

        async with self.bot.pool.acquire() as conn:
            guild = await conn.fetchrow("SELECT * FROM guilds WHERE id = $1",ctx.channel.guild.id)

            try:
                modrole = ctx.guild.get_role(guild['modrole'])
                pingable = []
                for x in modrole.members:
                    if x.status != discord.Status.online:
                        continue
                    pingable.append(x.id)
                        
                
                await ctx.channel.send(f"<@{random.choice(pingable)}>, **{ctx.author}** has a requested a moderator.",embed=embed)
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )


def setup(bot):
    bot.add_cog(config(bot))
