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

import asyncio
import csv
import math
import os
import random
import re
import sys
from base64 import decode
from datetime import datetime
from io import BytesIO
from textwrap import dedent

import aiohttp
import aioredis
import arrow
import asyncpg
import config
import discord
import requests
from discord.ext import commands
from gtrans import translate_text
from textblob import TextBlob

from wrenchboat.utils.modlogs import modlogs


class utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="userinfo",)
    async def _userinfo(self, ctx, user: discord.Member = None):
        if user is None:
            user = ctx.author

        embed = discord.Embed(color=0x99AAB5)
        embed.set_author(name=user, icon_url=user.avatar_url)
        embed.set_thumbnail(url=user.avatar_url)
        embed.add_field(
            name="User Information",
            value=f"Id: {user.id}\nProfile: {user.mention}\nCreated: {arrow.get(user.created_at).humanize()} ({user.created_at})",
            inline=False,
        )
        embed.add_field(
            name="Member Information",
            value=f"Joined: {arrow.get(user.joined_at).humanize()} ({user.joined_at})",
            inline=False,
        )
        embed.add_field(
            name="Infractions",
            value=f"Total Infractions: {await self.bot.pool.fetchval('SELECT COUNT(*) FROM infractions WHERE guild = $1 AND target = $2',ctx.channel.guild.id,user.id)}\nUnique Servers: {await self.bot.pool.fetchval('SELECT COUNT(DISTINCT guild) FROM infractions WHERE target = $1',user.id)}",
        )

        try:
            await ctx.channel.send(embed=embed)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

    @commands.command(name="serverinfo")
    async def _serverinfo(self, ctx):

        embed = discord.Embed(color=0x99AAB5)
        embed.set_author(name=ctx.guild.name, icon_url=ctx.guild.icon_url)
        embed.set_thumbnail(url=ctx.guild.icon_url)
        embed.add_field(
            name="Server Information",
            value=f"Id: {ctx.channel.guild.id}\nMembers: {ctx.channel.guild.member_count:,d}\nCreated: {arrow.get(ctx.channel.guild.created_at).humanize()} ({ctx.channel.guild.created_at})",
            inline=False,
        )
        embed.add_field(
            name="Owner Information",
            value=f"Id: {ctx.channel.guild.owner.id}\nProfile: {ctx.channel.guild.owner.mention}\nCreated: {arrow.get(ctx.channel.guild.owner.created_at).humanize()} ({ctx.channel.guild.owner.created_at})",
            inline=False,
        )
        embed.add_field(
            name="Infractions",
            value=f"Total Infractions: {await self.bot.pool.fetchval('SELECT COUNT(*) FROM infractions WHERE guild = $1',ctx.channel.guild.id)}",
            inline=False,
        )

        try:
            await ctx.channel.send(embed=embed)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

    @commands.command(name="avy",)
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

    @commands.command(name="sql",)
    @commands.is_owner()
    async def _sql(self, ctx, *, statement):
        async with self.bot.pool.acquire() as conn:
            try:
                await conn.fetchrow(statement)
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(":ok_hand:")

    @commands.command(name="bug",)
    async def _bug(self, ctx):

        return await ctx.channel.send(
            "You can report a bug here: --> <https://rb.gy/h2kktv>! Thank you in advance"
        )

    @commands.command(name="support",)
    async def _support(self, ctx):

        return await ctx.channel.send(
            f"You can join our support server @: {config.support}"
        )

    """
    highligher
    """

    @commands.group(
        name="highlight", invoke_without_command=True, aliases=["hl"],
    )
    async def _highlight(self, ctx):
        return

    @_highlight.command()
    async def _add(self, ctx, *, word: str):

        if len(word) > 2000:
            return await ctx.channel.send(
                "Nope. Not gonna do it. No, no no. (Word or prhase too long)"
            )

        async with self.bot.pool.acquire() as conn:
            highlight = await conn.fetchrow(
                "SELECT * FROM highlights WHERE author = $1 AND guild = $2 AND phrase = $3",
                ctx.author.id,
                ctx.channel.guild.id,
                word.lower(),
            )

            if highlight:
                return await ctx.channel.send(
                    "No go!!!!! That word is already highlighted"
                )

            try:
                i = await conn.fetchrow(
                    f"INSERT INTO highlights(author,guild,phrase) VALUES($1,$2,$3) RETURNING *",
                    ctx.author.id,
                    ctx.channel.guild.id,
                    word.lower(),
                )
                self.bot.highlights[i["id"]] = {
                    "phrase": i["phrase"],
                    "author": i["author"],
                    "guild": i["guild"],
                }
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(f":ok_hand:")

    @_highlight.command(name="delete",)
    async def _delete(self, ctx, *, word: str):
        async with self.bot.pool.acquire() as conn:
            highlight = await conn.fetchrow(
                "SELECT * FROM highlights WHERE author = $1 AND guild = $2 AND phrase = $3",
                ctx.author.id,
                ctx.channel.guild.id,
                word.lower(),
            )

            if not highlight:
                return await ctx.channel.send(
                    "Couldn't that highlighted phrase or word... "
                )

            try:
                await conn.fetchrow(
                    f"DELETE FROM highlights WHERE author = $1 AND guild = $2 AND phrase = $3",
                    ctx.author.id,
                    ctx.channel.guild.id,
                    word.lower(),
                )
                del self.bot.highlights[highlight["id"]]
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(f":ok_hand: (deleted ig)")

    @_highlight.command(name="clear")
    async def _clear(self, ctx):
        async with self.bot.pool.acquire() as conn:
            try:
                await conn.fetchrow(
                    f"DELETE FROM highlights WHERE author = $1 AND guild = $2",
                    ctx.author.id,
                    ctx.channel.guild.id,
                )
                for x in sorted(self.bot.highlights):
                    if (
                        self.bot.highlights[x]["author"] == ctx.author.id
                        and self.bot.highlights[x]["guild"] == ctx.guild.id
                    ):
                        del self.bot.highlights[x]
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(f":ok_hand: I deleted all your highlighted words!!!")

    @commands.group(
        name="emoji", invoke_without_command=True,
    )
    async def _emoji(self, ctx, emoji: discord.PartialEmoji):

        await ctx.channel.send(emoji.url)

    @_emoji.command(
        name="add",
        usage="(add attachment)",
        description="Add an emoji to your server without going through Discord's UI",
    )
    @commands.has_permissions(manage_emojis=True)
    async def _add(self, ctx, *, name=None):

        attachment = ctx.message.attachments
        if not attachment:
            return await ctx.channel.send(
                "Did you read my usage? SMH. Add an attachment to be used."
            )

        try:
            response = requests.get(attachment[0].url)
            emoji = await ctx.channel.guild.create_custom_emoji(
                name=attachment[0].filename[:32] if name is None else name,
                image=BytesIO(response.content).getvalue(),
                reason=f"Emoji added on the fly by: {ctx.author}",
            )
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(f"{emoji}")

    @_emoji.command(name="delete",)
    @commands.has_permissions(manage_emojis=True)
    async def _delete(self, ctx, *, emoji: discord.Emoji):

        try:
            await emoji.delete(
                reason=f"Emoji: {emoji.name} ({emoji.id}) deleted by: {ctx.author} ({ctx.author.id})"
            )
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(f":ok_hand:")

    @commands.command(name="invite")
    async def _invite(self, ctx, invite: discord.Invite):

        invite = await self.bot.fetch_invite(invite, with_counts=True)
        embed = discord.Embed(color=0x99AAB5, description=invite.guild.description)
        embed.set_author(name=invite.guild, icon_url=invite.guild.icon_url)
        embed.set_thumbnail(url=invite.guild.icon_url)
        embed.add_field(
            name="Guild Information",
            value=f"Id: {invite.guild.id}\nCreated At: {arrow.get(invite.guild.created_at).humanize()} ({invite.guild.created_at})",
        )

        await ctx.channel.send(embed=embed)

    @commands.command(name="jellybean",)
    async def _jellybean(self, ctx):

        await ctx.channel.send("https://youtu.be/D7eQzUrUMvU")

    @commands.command(name="topic",)
    @commands.has_permissions(manage_channels=True)
    async def _topic(self, ctx):

        try:
            if ctx.channel.topic is None:
                return
            await ctx.channel.send(
                f"**#{ctx.channel.name}**\n> {ctx.channel.topic}",
                allowed_mentions=discord.AllowedMentions(
                    everyone=False, roles=False, users=False
                ),
            )
        except Exception as err:
            print(err)

    @commands.command(name="snipe")
    async def _snipe(self, ctx):

        if not self.bot.snips.get(ctx.channel.id):
            return await ctx.channel.send("There is not snipes in this channnel :3")

        embed = discord.Embed(
            color=self.bot.snips[ctx.channel.id]["author"].color,
            description=self.bot.snips[ctx.channel.id]["content"],
            timestamp=self.bot.snips[ctx.channel.id]["message_created"],
        )
        embed.set_author(name=f"{ctx.author.display_name} sniped a message!")
        embed.set_footer(
            text=self.bot.snips[ctx.channel.id]["author"],
            icon_url=self.bot.snips[ctx.channel.id]["author"].avatar_url,
        )

        await ctx.channel.send(embed=embed)
        del self.bot.snips[ctx.channel.id]

    @commands.command(name="trasnlatembed", aliases=["translateembed", "tembed"])
    async def _translateembed(self, ctx, message: discord.Message):

        if not message.embeds:
            return await ctx.channel.send(
                "That's weird... I couldn't find any embeds on that message!!!"
            )

        field_list = []
        old_embed = message.embeds[0].to_dict()
        if old_embed.get("description"):
            old_embed["description"] = str(
                TextBlob(old_embed["description"]).translate(to="en")
            )
        if old_embed.get("title"):
            old_embed["title"] = str(TextBlob(old_embed["title"]).translate(to="en"))
        if old_embed.get("author"):
            old_embed["author"]["name"] = str(
                TextBlob(old_embed["author"]["name"]).translate(to="en")
            )
        if old_embed.get("footer"):
            old_embed["footer"]["text"] = str(
                TextBlob(old_embed["footer"]["text"]).translate(to="en")
            )
        if old_embed.get("fields"):
            for x in range(len(old_embed["fields"])):
                field_list.append(
                    {
                        "name": str(
                            TextBlob(old_embed["fields"][x]["name"]).translate(to="en")
                        ),
                        "value": str(
                            TextBlob(old_embed["fields"][x]["value"]).translate(to="en")
                        ),
                    }
                )

            old_embed["fields"] = field_list
        new_embed = discord.Embed.from_dict(data=old_embed)
        await ctx.channel.send(embed=new_embed)

    @commands.command(name="translate")
    async def _translate(self, ctx, *, statement):

        if len(statement) > 1500:
            return await ctx.channel.send("No. Use less than 1500 characters idot.")

        embed = discord.Embed(
            color=ctx.author.color,
            description=str(TextBlob(statement).translate(to="en")),
        )
        embed.set_author(
            name=f"Triggered by {ctx.author.name}", icon_url=ctx.author.avatar_url
        )
        await ctx.channel.send(embed=embed)


def setup(bot):
    bot.add_cog(utility(bot))
