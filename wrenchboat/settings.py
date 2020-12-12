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


class settings(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="modlogs",
        usage="<#channel>",
        description="Sets your server's modlogs. The decancer command will also be logged here.",
    )
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

    @commands.command(
        name="messagelogs",
        usage="<#channel>",
        description="Set your server's message logs. Where messages that are deleted, pinned, or edited will be logged.",
    )
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

    @commands.command(
        name="serverlogs",
        usage="<#channel>",
        description="Set your server's servers logs. General server actions will be logged here.",
    )
    @commands.has_permissions(administrator=True)
    async def _messagelogs(self, ctx, *, channel: discord.TextChannel = None):
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

    @commands.command(
        name="responsetype",
        usage="<advanced,simple,normal,compact>",
        description="Set your server's inline response type.",
    )
    @commands.has_permissions(administrator=True)
    async def response_type(self, ctx, *, response_type: str="advanced"):
        if response_type.lower() not in ['advanced','normal','compact','simple']:#,'even_simpler']:
            return await ctx.channel.send(f"Please provide a valid option. {', '.join(['advanced','basic','compact','simple'])}")

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

    @commands.command(name="language",usage="<iso code>",description="Set your server's language, used in inline responses.")
    @commands.has_permissions(administrator=True)
    async def language(self, ctx, *, language_code:str="en"):    
        supported_languages = ['en','es','la','it']
        if language_code.lower() not in supported_languages:
            return await ctx.channel.send(f"Please provide a valid option. {', '.join(supported_languages)}")

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

    @commands.command(
        name="archivecategory",
        usage="(category id)",
        description="Set your server's archive category. Essentially channels you archive will go here.",
    )
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
        name="antinvite",
        usage="<BAN, KICK, MUTE, DELETE>",
        description="Remove invites from your discord server with this epic machine! When enabled the bot will do the predefined action when a user curses",
        invoke_without_command=True,
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

    @_antinvite.command(
        name="disable", description="Disable antiprofanity for your server."
    )
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
        name="antiprofanity",
        usage="<BAN, KICK, MUTE, DELETE>",
        description="Enable antiprofainity on your server. When enabled the bot will do the predefined action when a user curses (:warning: THIS CAN BE HARSH)",
        invoke_without_command=True,
    )
    @commands.has_permissions(administrator=True)
    async def _antiprofanity(self, ctx, *, option):

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
                self.bot.automod[ctx.channel.guild.id]["antiprofanity"] = option.lower()
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(
                f"Cool. I set your server's antiprofanity to {option.lower()}"
            )

    @_antiprofanity.command(
        name="disable", description="Disable antiprofanity for your server."
    )
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

    @commands.command(
        name="modrole",
        description="Set your server's modrole. This is used for the `pingmod` command",
    )
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

    @commands.command(
        name="pingmod",
        description="Ping a random **online** moderator from your server's mod role (Inspired by Kitchen Sink)",
    )
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

    @commands.command(name="tokenr",description="Enable or Disable token remover.")
    @commands.has_permissions(administrator=True)
    async def _tokenr(self,ctx):
        disable = False
        if self.bot.automod[ctx.channel.guild.id]['token_remover']:
            code = ''.join([random.choice(string.ascii_letters + string.digits) for n in range(5)])
            original = await ctx.channel.send(f"This action is dangerous. To continue please type `{code}` by itself.")
            def check(m):
                return m.author == ctx.author and m.channel == ctx.channel

            msg = await self.bot.wait_for("message", check=check)

            if msg.content != code:
                embed = discord.Embed(description=f"This message is in response to [this message]({original.jump_url}). It was never answered.")
                return await ctx.channel.send(f"❌ Token remover will stay enabled. Failed to type the correct code.",embed=embed)
            disable = True
        
        async with self.bot.pool.acquire() as conn:
            try:
                await conn.execute("UPDATE guilds SET token_remover = $1 WHERE id = $2",True if not disable else False,ctx.channel.guild.id)
                self.bot.automod[ctx.channel.guild.id]['token_remover'] = True if not disable else False
                await ctx.channel.send(f"""Token remover has been set to: {"Enabled" if not disable else "Disabled"}""")
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

def setup(bot):
    bot.add_cog(settings(bot))
