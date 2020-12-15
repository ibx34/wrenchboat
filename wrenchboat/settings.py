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
import string
from discord.ext import commands

from wrenchboat.utils import pagination
from wrenchboat.utils.checks import checks
from wrenchboat.utils.modlogs import modlogs

seconds_per_unit = {"s": 1, "m": 60, "h": 3600}


def convert_to_seconds(s):
    return int(s[:-1]) * seconds_per_unit[s[-1]]


class settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="prefixes", aliases=["prefix"], invoke_without_command=True)
    async def _wrench_prefix(self, ctx):

        prefixes = await self.bot.pool.fetchrow(
            "SELECT * FROM guilds WHERE id = $1", ctx.channel.guild.id
        )
        list = [f"{prefixes['prefixes'].index(x)}. {x}" for x in prefixes["prefixes"]]
        embed = discord.Embed(
            description="\n".join(list), title=f"{ctx.channel.guild}'s prefixes"
        )

        await ctx.channel.send(embed=embed)

    @_wrench_prefix.command(name="add")
    @commands.has_permissions(administrator=True)
    async def _wrench_prefixes_add(self, ctx, *, prefix: str):
        if len(prefix) > 30:
            return await ctx.channel.send(
                "Prefixes may not be over **30** characters long."
            )

        async with self.bot.pool.acquire() as conn:
            guild_data = await self.bot.pool.fetchrow(
                "SELECT * FROM guilds WHERE id = $1", ctx.channel.guild.id
            )

            if len(guild_data["prefixes"]) > 30:
                return await ctx.channel.send(
                    f"You can't have more than **30** prefixes!!!! CALM DOWN PLEASE!!!!!!!"
                )

            if prefix in guild_data["prefixes"]:
                return await ctx.channel.send(
                    f"That prefix is already in your server's list. You can remove it with `{ctx.prefix}prefix remove {prefix.lower()}`"
                )

            try:
                old_prefixes = [x for x in guild_data["prefixes"]]
                old_prefixes.append(prefix)
                new_prefixes = await conn.fetchrow(
                    "UPDATE guilds SET prefixes = $1 WHERE id = $2 RETURNING *",
                    old_prefixes,
                    ctx.channel.guild.id,
                )
                self.bot.prefixes[ctx.channel.guild.id] = new_prefixes["prefixes"]
                list = [
                    f"{new_prefixes['prefixes'].index(x)}. {x}"
                    for x in new_prefixes["prefixes"]
                ]
                embed = discord.Embed(
                    description="\n".join(list),
                    title=f"Updated {ctx.channel.guild}'s prefixes",
                )
                await ctx.channel.send(embed=embed)
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

    @_wrench_prefix.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def _wrench_prefixes_remove(self, ctx, *, prefix: str):
        if len(prefix) > 30:
            return await ctx.channel.send(
                "Prefixes may not be over **30** characters long."
            )

        async with self.bot.pool.acquire() as conn:
            guild_data = await self.bot.pool.fetchrow(
                "SELECT * FROM guilds WHERE id = $1", ctx.channel.guild.id
            )

            if prefix not in guild_data["prefixes"] or prefix.lower() in [
                "wrench",
                "w!",
            ]:
                return await ctx.channel.send(
                    f"That prefix is not in your server's list. You can remove it with `{ctx.prefix}prefix add {prefix.lower()}`"
                )

            try:
                old_prefixes = [x for x in guild_data["prefixes"]]
                old_prefixes.remove(prefix)
                new_prefixes = await conn.fetchrow(
                    "UPDATE guilds SET prefixes = $1 WHERE id = $2 RETURNING *",
                    old_prefixes,
                    ctx.channel.guild.id,
                )
                self.bot.prefixes[ctx.channel.guild.id] = new_prefixes["prefixes"]
                list = [
                    f"{new_prefixes['prefixes'].index(x)}. {x}"
                    for x in new_prefixes["prefixes"]
                ]
                embed = discord.Embed(
                    description="\n".join(list),
                    title=f"Updated {ctx.channel.guild}'s prefixes",
                )
                await ctx.channel.send(embed=embed)
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

    @commands.command(name="modlogs",)
    @commands.has_permissions(administrator=True)
    async def _modlogs(self, ctx, *, channel: discord.TextChannel = None):
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

    @commands.command(name="messagelogs",)
    @commands.has_permissions(administrator=True)
    async def _messagelogs(self, ctx, *, channel: discord.TextChannel = None):
        async with self.bot.pool.acquire() as conn:
            try:
                await conn.execute(
                    "UPDATE guilds SET messagelogs = $1 WHERE id = $2",
                    None if channel is None else channel.id,
                    ctx.channel.guild.id,
                )

                self.bot.logging[ctx.channel.guild.id]["message_logs"] = (
                    None if channel is None else channel.id
                )
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(
                f"""OMG THAT TOOK EFFORT!!!! I set your message logs to {channel.mention if channel is not None else "Disabled"}."""
            )

    @commands.command(name="automodlogs",)
    @commands.has_permissions(administrator=True)
    async def _automodlogs(self, ctx, *, channel: discord.TextChannel = None):
        async with self.bot.pool.acquire() as conn:
            try:
                await conn.execute(
                    "UPDATE guilds SET automodlogs = $1 WHERE id = $2",
                    None if channel is None else channel.id,
                    ctx.channel.guild.id,
                )

                self.bot.logging[ctx.channel.guild.id]["automod_logs"] = (
                    None if channel is None else channel.id
                )
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(
                f"""OMG THAT TOOK EFFORT!!!! I set your automod logs to {channel.mention if channel is not None else "Disabled"}."""
            )

    @commands.command(name="serverlogs",)
    @commands.has_permissions(administrator=True)
    async def _serverlogs(self, ctx, *, channel: discord.TextChannel = None):
        async with self.bot.pool.acquire() as conn:
            try:
                await conn.execute(
                    "UPDATE guilds SET serverlogs = $1 WHERE id = $2",
                    None if channel is None else channel.id,
                    ctx.channel.guild.id,
                )

                self.bot.logging[ctx.channel.guild.id]["server_logs"] = (
                    None if channel is None else channel.id
                )
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(
                f"""OMG THAT TOOK EFFORT!!!! I set your message logs to {channel.mention if channel is not None else "Disabled"}."""
            )

    @commands.command(name="responsetype",)
    @commands.has_permissions(administrator=True)
    async def response_type(self, ctx, *, response_type: str = "advanced"):
        if response_type.lower() not in [
            "advanced",
            "normal",
            "compact",
            "simple",
        ]:  # ,'even_simpler']:
            return await ctx.channel.send(
                f"Please provide a valid option. {', '.join(['advanced','basic','compact','simple'])}"
            )

        async with self.bot.pool.acquire() as conn:
            try:
                await conn.execute(
                    "UPDATE guilds SET response_type = $1 WHERE id = $2",
                    response_type.lower(),
                    ctx.channel.guild.id,
                )

                self.bot.guild_responses[ctx.channel.guild.id] = response_type
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(
                f"Your server's response type has been set to {response_type}"
            )

    @commands.command(name="language")
    @commands.has_permissions(administrator=True)
    async def language(self, ctx, *, language_code: str = "en"):
        supported_languages = ["en", "es", "la", "it"]
        if language_code.lower() not in supported_languages:
            return await ctx.channel.send(
                f"Please provide a valid option. {', '.join(supported_languages)}"
            )

        async with self.bot.pool.acquire() as conn:
            try:
                await conn.execute(
                    "UPDATE guilds SET language = $1 WHERE id = $2",
                    language_code.lower(),
                    ctx.channel.guild.id,
                )
                self.bot.language[ctx.channel.guild.id] = language_code
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(
                f"Your server's language has been set to {language_code}"
            )

    @commands.command(name="archivecategory",)
    @commands.has_permissions(administrator=True)
    async def _archive_category(self, ctx, *, channel: discord.CategoryChannel = None):
        async with self.bot.pool.acquire() as conn:
            try:
                await conn.execute(
                    "UPDATE guilds SET archive_category = $1 WHERE id = $2",
                    None if channel is None else channel.id,
                    ctx.channel.guild.id,
                )
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(
                f"""Ight, I set your server's "archive category" to {channel.name if channel is not None else "Disabled"}."""
            )

    @commands.command(name="muterole",)
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

    @commands.command(name="dontmuterole",)
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

    @commands.command(name="antihoist",)
    @commands.has_permissions(administrator=True)
    async def _antihoist(self, ctx):
        async with self.bot.pool.acquire() as conn:

            try:
                update = await conn.fetchrow(
                    "UPDATE guilds SET antihoist = $1 WHERE id = $2 RETURNING *",
                    False
                    if self.bot.automod[ctx.channel.guild.id]["antihoist"]
                    else True,
                    ctx.channel.guild.id,
                )
                self.bot.automod[ctx.channel.guild.id]["antihoist"] = update[
                    "antihoist"
                ]
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send("👌")

    @commands.group(
        name="antinvite", invoke_without_command=True,
    )
    @commands.has_permissions(administrator=True)
    async def _antinvite(self, ctx, *, option):

        if option.lower() not in ["ban", "mute", "kick", "delete"]:
            return await ctx.channel.send(
                "**BRUH** provide an actual action my guy... (Actions: warn, kick, mute)"
            )

        async with self.bot.pool.acquire() as conn:

            try:
                await conn.execute(
                    "UPDATE guilds SET antinvite = $1 WHERE id = $2",
                    option.lower(),
                    ctx.channel.guild.id,
                )
                self.bot.automod[ctx.channel.guild.id]["antinvite"] = option.lower()
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(
                f"Cool. I set your server's antinvite to {option.lower()}"
            )

    @_antinvite.command(name="disable")
    @commands.has_permissions(administrator=True)
    async def _antinvite_disable(self, ctx):

        async with self.bot.pool.acquire() as conn:

            try:
                await conn.execute(
                    "UPDATE guilds SET antinvite = $1 AND id = $2",
                    None,
                    ctx.channel.guild.id,
                )
                del self.bot.automod[ctx.channel.guild.id]["antinvite"]
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(f"👍")

    @commands.group(
        name="antiprofanity", invoke_without_command=True,
    )
    @commands.has_permissions(administrator=True)
    async def _antiprofanity(self, ctx, *, option):

        if option.lower() not in ["ban", "mute", "kick", "delete"]:
            return await ctx.channel.send(
                "**BRUH** provide an actual action my guy... (Actions: warn, kick, mute,ban)"
            )

        async with self.bot.pool.acquire() as conn:

            try:
                await conn.execute(
                    "UPDATE guilds SET antiprofanity = $1 WHERE id = $2",
                    option.lower(),
                    ctx.channel.guild.id,
                )
                self.bot.automod[ctx.channel.guild.id]["antiprofanity"] = option.lower()
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(
                f"Cool. I set your server's antiprofanity to {option.lower()}"
            )

    @_antiprofanity.command(name="disable")
    @commands.has_permissions(administrator=True)
    async def _antiprofanity_disable(self, ctx):

        async with self.bot.pool.acquire() as conn:

            try:
                await conn.execute(
                    "UPDATE guilds SET antiprofanity = $1 AND id = $2",
                    None,
                    ctx.channel.guild.id,
                )
                del self.bot.automod[ctx.channel.guild.id]["antiprofanity"]
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(f"👍")

    @commands.command(name="modrole",)
    @commands.has_permissions(administrator=True)
    async def _modrole(self, ctx, role: discord.Role = None):
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

    @commands.group(name="antimassping", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def _antimassping(self, ctx, action: str, amount: int = 3):

        if action.lower() not in ["ban", "mute", "kick", "delete"]:
            return await ctx.channel.send(
                "**BRUH** provide an actual action my guy... (Actions: warn, kick, mute,ban)"
            )

        async with self.bot.pool.acquire() as conn:

            try:
                await conn.execute(
                    "UPDATE guilds SET antimassping = $1 WHERE id = $2",
                    f"{action.lower()}|{amount}",
                    ctx.channel.guild.id,
                )
                self.bot.automod[ctx.channel.guild.id]["antimassping"] = {
                    "amount": amount,
                    "action": action.lower(),
                }
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(
                f"Cool. I set your server's antimassping to {action.lower()}"
            )

    @_antimassping.command(name="disable",)
    @commands.has_permissions(administrator=True)
    async def _antimassping_disable(self, ctx):

        async with self.bot.pool.acquire() as conn:

            try:
                await conn.execute(
                    "UPDATE guilds SET antimassping = $1 AND id = $2",
                    None,
                    ctx.channel.guild.id,
                )
                del self.bot.automod[ctx.channel.guild.id]["antimassping"]
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(f"👍")

    @commands.command(name="pingmod",)
    async def _pingmod(self, ctx, *, message):

        embed = discord.Embed(
            color=0x99AAB5, description=message, timestmap=datetime.utcnow()
        )
        embed.set_footer(
            text=f"{ctx.author} | {ctx.author.id}", icon_url=ctx.author.avatar_url
        )

        async with self.bot.pool.acquire() as conn:
            guild = await conn.fetchrow(
                "SELECT * FROM guilds WHERE id = $1", ctx.channel.guild.id
            )

            try:
                modrole = ctx.guild.get_role(guild["modrole"])
                pingable = []
                for x in modrole.members:
                    if x.status != discord.Status.online:
                        continue
                    pingable.append(x.id)

                await ctx.channel.send(
                    f"<@{random.choice(pingable)}>, **{ctx.author}** has a requested a moderator.",
                    embed=embed,
                )
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

    @commands.command(name="tokenr")
    @commands.has_permissions(administrator=True)
    async def _tokenr(self, ctx):
        disable = False
        if self.bot.automod[ctx.channel.guild.id]["token_remover"]:
            code = "".join(
                [random.choice(string.ascii_letters + string.digits) for n in range(5)]
            )
            original = await ctx.channel.send(
                f"This action is dangerous. To continue please type `{code}` by itself."
            )

            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            msg = await self.bot.wait_for("message", check=check)

            if msg.content != code:
                embed = discord.Embed(
                    description=f"This message is in response to [this message]({original.jump_url}). It was never answered."
                )
                return await ctx.channel.send(
                    f"❌ Token remover will stay enabled. Failed to type the correct code.",
                    embed=embed,
                )
            disable = True

        async with self.bot.pool.acquire() as conn:
            try:
                await conn.execute(
                    "UPDATE guilds SET token_remover = $1 WHERE id = $2",
                    True if not disable else False,
                    ctx.channel.guild.id,
                )
                self.bot.automod[ctx.channel.guild.id]["token_remover"] = (
                    True if not disable else False
                )
                await ctx.channel.send(
                    f"""Token remover has been set to: {"Enabled" if not disable else "Disabled"}"""
                )
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )


def setup(bot):
    bot.add_cog(settings(bot))
