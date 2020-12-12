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

from datetime import datetime
from textwrap import dedent

import config
import discord
from discord.ext import commands

class _purge(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        name="purge",
        invoke_without_command=True,
        usage="(amount)",
        description="Purge an amount of messages from a channel. (Pinned messages are ignored).",
        aliases=["prune", "clear", "massdelete"],
    )
    @commands.has_permissions(manage_messages=True)
    async def _purge(self, ctx, amount: int):
        def is_pinned(m):
            return not m.pinned

        try:
            purged = await ctx.channel.purge(limit=amount+1, check=is_pinned)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"I have purged **{len(purged)}** messages. *Say thank you*"
        )

    @_purge.command(
        name="from",
        usage="@user (amount)",
        description="Purge an amount of message from a channel that a certain user sent.",
    )
    @commands.has_permissions(manage_messages=True)
    async def _from(self, ctx, user: discord.Member, amount: int):
        def is_x(m):
            return m.author == user

        try:
            purged = await ctx.channel.purge(limit=amount+1, check=is_x)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"I have purged **{len(purged)}** messages from {user}. *You better say thank you*"
        )

    @_purge.command(
        name="bot",
        usage="(amount)",
        description="Purge an amount of messages from a channel that were sent by a bot.",
    )
    @commands.has_permissions(manage_messages=True)
    async def _bot(self, ctx, amount: int):
        def is_bot(m):
            return m.author.bot

        try:
            purged = await ctx.channel.purge(limit=amount+1, check=is_bot)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"I have purged **{len(purged)}** messages that were from bots. *You better say thank you*"
        )

    @_purge.command(
        name="embed",
        usage="(amount)",
        description="Purge an amount of messages from a channel that **include** embed(s)",
    )
    @commands.has_permissions(manage_messages=True)
    async def _embed(self, ctx, amount: int):
        def has_embed(m):
            return m.embeds

        try:
            purged = await ctx.channel.purge(limit=amount+1, check=has_embed)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"I have purged **{len(purged)}** messages that contained embeds. *You better say thank you*"
        )

    @_purge.command(
        name="contains",
        usage="(amount) (phrase to searh)",
        description="Purge an amount of messages from a channel that contain a certain phrase(s).",
    )
    @commands.has_permissions(manage_messages=True)
    async def _contains(self, ctx, amount: int, *, contains: str):
        def contains_x(m):
            return contains in m.content

        try:
            purged = await ctx.channel.purge(limit=int(amount)+1, check=contains_x)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"I have purged **{len(purged)}** messages that contained `{contains}`. *I'm serious this one took a lot to do, thank me*"
        )

    @_purge.command(
        name="reactions",
        usage="(amount) <reation>",
        description="Purge an amount of messages that have reactions or a certain reaction.",
    )
    @commands.has_permissions(manage_messages=True)
    async def _reactions(self, ctx, amount: int, reaction: str = None):
        def has_reactions(m):
            if reaction is not None:
                for x in m.reactions:
                    if str(x) == reaction:
                        return x
            else:
                return m.reactions

        try:
            purged = await ctx.channel.purge(limit=int(amount)+1, check=has_reactions)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"I have purged **{len(purged)}** messages that had {f'the reaction {reaction}' if reaction is not None else 'reactions.'} *This took me a lot of work :sad:*"
        )

    @_purge.command(
        name="mentions",
        usage="(amount) <mention>",
        description="Purge an amount of messages that mentions anyone or a certain someone",
    )
    @commands.has_permissions(manage_messages=True)
    async def _mentions(self, ctx, amount: int, member: discord.Member = None):
        def has_mentions(m):
            if member is not None:
                if member.id in m.mentions.id:
                    return member
            else:
                return m.mentions

        try:
            purged = await ctx.channel.purge(limit=int(amount)+1, check=has_mentions)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"I have purged **{len(purged)}** messages that {f'mentioned {member.mention} *no I didnt ping them <3*' if member is not None else 'had mentions in them'}",
            allowed_mentions=discord.AllowedMentions(everyone=False, users=False),
        )

    @_purge.command(
        name="caps",
        usage="(amount)",
        description="Purge an amount of messages that is in full caps",
    )
    @commands.has_permissions(manage_messages=True)
    async def _mentions(self, ctx, amount: int):
        def is_upper(m):
            return m.content.upper() == m.content

        try:
            purged = await ctx.channel.purge(limit=int(amount)+1, check=is_upper)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"I have purged **{len(purged)}** messages that had all caps in it."
        )

    @_purge.command(
        name="between",
        usage="(id 1) (id 2)",
        description="Purge an amount of messages that is between message **1** and message **2**",
    )
    @commands.has_permissions(manage_messages=True)
    async def _between(self, ctx, message1: discord.Message, message2: discord.Message):
        try:
            purged = await ctx.channel.purge(before=message2, after=message1)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"I have purged **{len(purged)}** messages that were between {message1.id} and {message2.id}"
        )

    @_purge.command(
        name="system",
        usage="(amount)",
        description="Purge an amount of message that were sent by system",
    )
    @commands.has_permissions(manage_messages=True)
    async def _system(self, ctx, amount: int):
        def is_system(m):
            return m.is_system()

        try:
            purged = await ctx.channel.purge(limit=int(amount)+1, check=is_system)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"I have purged **{len(purged)}** messages that were from system!"
        )

    @_purge.command(
        name="newusers",
        usage="(amount)",
        description="Purge an amount of message that were sent by new users",
    )
    @commands.has_permissions(manage_messages=True)
    async def _newusers(self, ctx, amount: int):
        def is_new(m):
            return m.author.joined_at > m.author.joined_at + datetime.timedelta(
                minutes=60
            )

        try:
            purged = await ctx.channel.purge(limit=int(amount)+1, check=is_new)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"I have purged **{len(purged)}** messages that were from users who recently joined!"
        )

    @_purge.command(
        name="attachments",
        usage="(amount)",
        description="Purge an amount of message that have attachments with them",
    )
    @commands.has_permissions(manage_messages=True)
    async def _attachments(self, ctx, amount: int):
        def has_attachments(m):
            return m.attachments

        try:
            purged = await ctx.channel.purge(limit=int(amount)+1, check=has_attachments)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"I have purged **{len(purged)}** messages that had attachments!"
        )

    @_purge.command(
        name="noroles",
        usage="(amount)",
        description="Purge an amount of message that the author has no roles",
    )
    @commands.has_permissions(manage_messages=True)
    async def no_roles(self,ctx,amount: int) -> int: 
        def has_no_roles(m):
            return m.author.roles == [ctx.guild.default_role]

        try:
            purged = await ctx.channel.purge(limit=int(amount)+1, check=has_no_roles)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"I have purged **{len(purged)}** messages where the author had no roles!"
        )

    @_purge.command(
        name="nonembeds",
        usage="(amount)",
        description="Purge an amount of message that dont have any embed(s)",
    )
    @commands.has_permissions(manage_messages=True)
    async def _nonembeds(self, ctx, amount: int):
        def has_no_embeds(m):
            return not m.embeds

        try:
            purged = await ctx.channel.purge(limit=int(amount)+1, check=has_no_embeds)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"I have purged **{len(purged)}** messages that didn't have an embed"
        )

    @_purge.command(
        name="unpinned",
        usage="(amount)",
        description="Purge an amount of message that aren't pinned",
    )
    @commands.has_permissions(manage_messages=True)
    async def _unpinned(self, ctx, amount: int):
        def not_pinned(m):
            return not m.pinned

        try:
            purged = await ctx.channel.purge(limit=int(amount)+1, check=not_pinned)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"I have purged **{len(purged)}** messages that weren't pinned"
        )
        
def setup(bot):
    bot.add_cog(_purge(bot))
