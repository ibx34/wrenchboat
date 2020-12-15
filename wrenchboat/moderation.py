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
import math
from discord.ext import commands

from wrenchboat.utils import pagination
from wrenchboat.utils.checks import checks
from wrenchboat.utils.modlogs import modlogs
from wrenchboat.utils.responses import Responder
import typing

id = datetime.utcnow().strftime("%Y%m%d%H%M%S%f")


class moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="massban")
    @commands.has_permissions(ban_members=True)
    async def _massban(
        self,
        ctx,
        users: commands.Greedy[discord.Member],
        *,
        reason="No reason provided. You can add a reason with `case <id> <reason>`.",
    ):

        userslist = ", ".join(x.name for x in users)
        try:
            for x in users:
                await x.ban(reason=f"[{ctx.author}]: {reason}")
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(f"The following users have neen banned: {userslist}.")

    @commands.command(name="masskick")
    @commands.has_permissions(kick_members=True)
    async def _masskick(
        self,
        ctx,
        users: commands.Greedy[discord.Member],
        *,
        reason="No reason provided. You can add a reason with `case <id> <reason>`.",
    ):

        userslist = ", ".join(x.name for x in users)
        try:
            for x in users:
                await x.kick(reason=f"[{ctx.author}]: {reason}")
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(f"The following users have neen kicked: {userslist}.")

    @commands.command(name="massmute")
    @commands.has_permissions(kick_members=True)
    async def _massmute(
        self,
        ctx,
        users: commands.Greedy[discord.Member],
        *,
        reason="No reason provided. You can add a reason with `case <id> <reason>`.",
    ):

        if len(users) > 5:
            return await ctx.channel.send(
                "No go my guy!!! This command has a limit of 5 users for **everyone**, sorry."
            )

        userslist = ", ".join(x.name for x in users)
        async with ctx.bot.pool.acquire() as conn:
            mute = await conn.fetchrow(
                "SELECT * FROM guilds WHERE id = $1", ctx.channel.guild.id
            )

            try:
                mutedlist = []
                muterole = ctx.channel.guild.get_role(mute["muterole"])
                dontmuterole = ctx.channel.guild.get_role(mute["dontmute"])

                for x in users:
                    if dontmuterole in x.roles:
                        continue
                    await x.add_roles(muterole, reason=f"[{ctx.author}]: {reason}")
                    mutedlist.append(x)
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            userslist = ", ".join(x.name for x in mutedlist)
            await ctx.channel.send(f"The following users have neen muted: {userslist}.")

    @commands.command(
        name="ban", aliases=["banne", "disagreeing", "vac", "banish"],
    )
    @commands.has_permissions(ban_members=True)
    async def _ban(
        self,
        ctx,
        user: discord.Member,
        *,
        reason="No reason provided. You can add a reason with `case <id> <reason>`.",
    ):

        if not checks.above(self.bot, user, ctx.author):
            return

        try:
            await user.ban(reason=reason)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(f"{user} has been banned.")
        await modlogs(
            self=self.bot,
            moderator=ctx.author,
            user=user,
            reason=reason,
            type=ctx.command.name.capitalize(),
            case=None,
            time=datetime.utcnow(),
        )

    @commands.command(name="unban",)
    @commands.has_permissions(ban_members=True)
    async def _unban(
        self,
        ctx,
        user: int,
        *,
        reason="No reason provided. You can add a reason with `case <id> <reason>`.",
    ):

        try:
            user = await self.bot.fetch_user(user)
            await ctx.guild.unban(user, reason=reason)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(f"{user} has been unbanned.")
        await modlogs(
            self=self.bot,
            moderator=ctx.author,
            user=user,
            reason=reason,
            type=ctx.command.name.capitalize(),
            case=None,
            time=datetime.utcnow(),
        )

    @commands.command(name="softban",)
    @commands.has_permissions(ban_members=True)
    async def _softban(
        self,
        ctx,
        user: discord.Member,
        *,
        reason="No reason provided. You can add a reason with `case <id> <reason>`.",
    ):

        if not checks.above(self.bot, user, ctx.author):
            return

        try:
            await user.ban(reason=reason, delete_message_days=7)
            await user.unban(reason=reason)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(f"{user} has been soft banned.")
        await modlogs(
            self=self.bot,
            moderator=ctx.author,
            user=user,
            reason=reason,
            type=ctx.command.name.capitalize(),
            case=None,
            time=datetime.utcnow(),
        )

    @commands.command(name="forceban",)
    @commands.has_permissions(ban_members=True)
    async def _forceban(
        self,
        ctx,
        user: int,
        *,
        reason="No reason provided. You can add a reason with `case <id> <reason>`.",
    ):

        try:
            user = await self.bot.fetch_user(user)
            await ctx.guild.ban(user=user, reason=reason)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(f"{user} has been banned. (They're not in the guild).")
        await modlogs(
            self=self.bot,
            moderator=ctx.author,
            user=user,
            reason=reason,
            type=ctx.command.name.capitalize(),
            case=None,
            time=datetime.utcnow(),
        )

    @commands.command(name="kick",)
    @commands.has_permissions(kick_members=True)
    async def _kick(
        self,
        ctx,
        user: discord.Member,
        *,
        reason="No reason provided. You can add a reason with `case <id> <reason>`.",
    ):

        if not checks.above(self.bot, user, ctx.author):
            return

        try:
            await user.kick(reason=reason)
        except:
            return await ctx.channel.send("Something went wrong :/")

        await ctx.channel.send(f"{user} has been kicked.")
        await modlogs(
            self=self.bot,
            moderator=ctx.author,
            user=user,
            reason=reason,
            type=ctx.command.name.capitalize(),
            case=None,
            time=datetime.utcnow(),
        )

    @commands.group(name="warn", inovoke_without_command=True)
    @commands.has_permissions(kick_members=True)
    async def _warn(
        self, ctx, user: discord.Member, *, reason,
    ):

        if not checks.above(self.bot, user, ctx.author):
            return

        try:
            await user.send(
                f"You've been warning in **{ctx.guild.name}** for:\n{reason}"
            )
        except:
            pass

        await Responder.in_line(
            ctx=ctx, user=user, action=ctx.command.name, reason=reason
        )
        await modlogs(
            self=self.bot,
            moderator=ctx.author,
            user=user,
            reason=reason,
            type=ctx.command.name.capitalize(),
            case=None,
            time=datetime.utcnow(),
        )

    @_warn.command(name="nonotify", aliases=["nn"])
    @commands.has_permissions(kick_members=True)
    async def _warn_nonotify(
        self, ctx, user: discord.Member, *, reason,
    ):

        if not checks.above(self.bot, user, ctx.author):
            return

        await ctx.channel.send(
            f"**{ctx.channel.guild}** | {ctx.author} warned {user} for Indefinitely. ({reason})"
        )
        await modlogs(
            self=self.bot,
            moderator=ctx.author,
            user=user,
            reason=reason,
            type=ctx.command.name.capitalize(),
            case=None,
            time=datetime.utcnow(),
        )

    @commands.command(name="mute")
    @commands.has_permissions(manage_messages=True)
    async def _mute(
        self,
        ctx,
        user: discord.Member,
        *,
        reason="No reason provided. You can add a reason with `case <id> <reason>`.",
    ):

        if not checks.above(self.bot, user, ctx.author):
            return

        async with ctx.bot.pool.acquire() as conn:
            mute = await conn.fetchrow(
                "SELECT * FROM guilds WHERE id = $1", ctx.channel.guild.id
            )

            try:
                muterole = ctx.channel.guild.get_role(mute["muterole"])
                dontmuterole = ctx.channel.guild.get_role(mute["dontmute"])

                if dontmuterole in user.roles:
                    return await ctx.channel.send(
                        f"Idiots some days. You can't mute {user}, they got the sepcial don't mute role."
                    )
                await user.add_roles(muterole)
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(f"{user} has been muted. (Okay?)")
            await modlogs(
                self=self.bot,
                moderator=ctx.author,
                user=user,
                reason=reason,
                type=ctx.command.name.capitalize(),
                case=None,
                time=datetime.utcnow(),
                role=muterole,
            )

    @commands.command(name="hardmute")
    @commands.has_permissions(manage_messages=True)
    async def _hardmute(
        self,
        ctx,
        user: discord.Member,
        *,
        reason="No reason provided. You can add a reason with `case <id> <reason>`.",
    ):

        if not checks.above(self.bot, user, ctx.author):
            return

        async with ctx.bot.pool.acquire() as conn:
            mute = await conn.fetchrow(
                "SELECT * FROM guilds WHERE id = $1", ctx.channel.guild.id
            )

            try:
                muterole = ctx.channel.guild.get_role(mute["muterole"])
                dontmuterole = ctx.channel.guild.get_role(mute["dontmute"])

                if dontmuterole in user.roles:
                    return await ctx.channel.send(
                        f"Idiots some days. You can't mute {user}, they got the sepcial don't mute role."
                    )
                for x in user.roles:
                    try:
                        await user.remove_roles(x)
                    except:
                        continue

                await user.add_roles(muterole)
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(f"{user} has been muted. (Okay?)")
            await modlogs(
                self=self.bot,
                moderator=ctx.author,
                user=user,
                reason=reason,
                type=ctx.command.name.capitalize(),
                case=None,
                time=datetime.utcnow(),
                role=muterole,
            )

    @commands.command(name="supermute")
    @commands.has_permissions(manage_messages=True)
    async def _supermute(
        self,
        ctx,
        user: discord.Member,
        *,
        reason="No reason provided. You can add a reason with `case <id> <reason>`.",
    ):

        if not checks.above(self.bot, user, ctx.author):
            return

        async with ctx.bot.pool.acquire() as conn:
            mute = await conn.fetchrow(
                "SELECT * FROM guilds WHERE id = $1", ctx.channel.guild.id
            )

            try:
                muterole = ctx.channel.guild.get_role(mute["muterole"])
                dontmuterole = ctx.channel.guild.get_role(mute["dontmute"])

                if dontmuterole in user.roles:
                    return await ctx.channel.send(
                        f"Idiots some days. You can't mute {user}, they got the sepcial don't mute role."
                    )
                await user.add_roles(muterole)
                await user.edit(
                    mute=True, reason=f"[Supermute by {ctx.author}]: {reason}"
                )
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(f"{user} has been muted. (Okay?)")
            await modlogs(
                self=self.bot,
                moderator=ctx.author,
                user=user,
                reason=reason,
                type=ctx.command.name.capitalize(),
                case=None,
                time=datetime.utcnow(),
                role=muterole,
            )

    @commands.command(name="massvoicemute")
    @commands.has_permissions(manage_messages=True)
    async def _massvoicemute(
        self,
        ctx,
        users: commands.Greedy[discord.Member],
        *,
        reason="No reason provided. You can add a reason with `case <id> <reason>`.",
    ):

        async with ctx.bot.pool.acquire() as conn:
            mute = await conn.fetchrow(
                "SELECT * FROM guilds WHERE id = $1", ctx.channel.guild.id
            )

            try:
                mutedlist = []
                dontmuterole = ctx.channel.guild.get_role(mute["dontmute"])

                for x in users:
                    if not checks.above(self.bot, x, ctx.author):
                        continue
                    if dontmuterole in x.roles:
                        continue
                    await x.edit(
                        mute=True, reason=f"[Massvoice mute by {ctx.author}]: {reason}"
                    )
                    mutedlist.append(x)
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            list = f"\n".join(f"{x} {x.id}" for x in mutedlist)
            if len(list) > 1700:
                await ctx.channel.send(
                    f""":ok_hand: I have muted {len(mutedlist)} members."""
                )
                for i in range(math.ceil(len(list) / 1992)):
                    chunk = list[(i - 1) * 1700 : i * 1992]
                    await ctx.channel.send(f"```\n{chunk}\n```")
            else:
                await ctx.channel.send(
                    f""":ok_hand: I have muted {len(mutedlist)} members.```{list}```"""
                )

    @commands.command(name="voicemute")
    @commands.has_permissions(manage_messages=True)
    async def _voicemute(
        self,
        ctx,
        user: discord.Member,
        *,
        reason="No reason provided. You can add a reason with `case <id> <reason>`.",
    ):

        if not checks.above(self.bot, user, ctx.author):
            return

        async with ctx.bot.pool.acquire() as conn:
            mute = await conn.fetchrow(
                "SELECT * FROM guilds WHERE id = $1", ctx.channel.guild.id
            )

            try:
                dontmuterole = ctx.channel.guild.get_role(mute["dontmute"])

                if dontmuterole in user.roles:
                    return await ctx.channel.send(
                        f"Idiots some days. You can't mute {user}, they got the sepcial don't mute role."
                    )
                await user.edit(
                    mute=True, reason=f"[ Voice mute by {ctx.author} ]: {reason}"
                )
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(f"{user} has been **voice** muted. (Okay?)")
            await modlogs(
                self=self.bot,
                moderator=ctx.author,
                user=user,
                reason=reason,
                type=ctx.command.name.capitalize(),
                case=None,
                time=datetime.utcnow(),
            )

    @commands.command(name="voiceunmute")
    @commands.has_permissions(manage_messages=True)
    async def _voiceunmute(
        self,
        ctx,
        user: discord.Member,
        *,
        reason="No reason provided. You can add a reason with `case <id> <reason>`.",
    ):

        if not checks.above(self.bot, user, ctx.author):
            return

        async with ctx.bot.pool.acquire() as conn:
            mute = await conn.fetchrow(
                "SELECT * FROM guilds WHERE id = $1", ctx.channel.guild.id
            )

            try:
                dontmuterole = ctx.channel.guild.get_role(mute["dontmute"])

                if dontmuterole in user.roles:
                    return await ctx.channel.send(
                        f"Idiots some days. You can't mute {user}, they got the sepcial don't mute role."
                    )
                await user.edit(
                    mute=False, reason=f"[ Voice unmute by {ctx.author} ]: {reason}"
                )
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(f"{user} has been **voice** unmuted. (Okay?)")
            await modlogs(
                self=self.bot,
                moderator=ctx.author,
                user=user,
                reason=reason,
                type=ctx.command.name.capitalize(),
                case=None,
                time=datetime.utcnow(),
            )

    @commands.command(name="unmute")
    @commands.has_permissions(manage_messages=True)
    async def _unmute(
        self,
        ctx,
        user: discord.Member,
        *,
        reason="No reason provided. You can add a reason with `case <id> <reason>`.",
    ):

        if not checks.above(self.bot, user, ctx.author):
            return

        async with ctx.bot.pool.acquire() as conn:
            mute = await conn.fetchrow(
                "SELECT * FROM guilds WHERE id = $1", ctx.channel.guild.id
            )

            try:
                muterole = ctx.channel.guild.get_role(mute["muterole"])
                await user.remove_roles(muterole)
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(f"{user} has been unmuted. (happy? mr. nice)")
            await modlogs(
                self=self.bot,
                moderator=ctx.author,
                user=user,
                reason=reason,
                type=ctx.command.name.capitalize(),
                case=None,
                time=datetime.utcnow(),
                role=muterole,
            )

    @commands.command(name="history")
    @commands.has_permissions(administrator=True)
    async def _history(self, ctx, user: discord.User = None):

        if user is None:
            user = ctx.author

        async with ctx.bot.pool.acquire() as conn:

            selected = await conn.fetch(
                "SELECT * FROM infractions WHERE target = $1 AND guild = $2",
                user.id,
                ctx.guild.id,
            )

            if not selected:
                return await ctx.channel.send("Nahhh, they have been good I guess..")

            pages = []

            for x in selected:
                moderator = await self.bot.fetch_user(x["moderator"])
                embed = discord.Embed(
                    color=0x99AAB5,
                    description=f"**Case** {x['id']} - {x['type']}\n**Time ago**: {arrow.get(x['time_punsihed']).humanize()}\n**Moderator**: {moderator} ({moderator.id})\n**Reason**: {x['reason']}",
                )
                embed.set_author(
                    name=f"{user.name}'s History", icon_url=user.avatar_url
                )
                pages.append(embed)

            paginator = pagination.BotEmbedPaginator(ctx, pages)
            return await paginator.run()

    @commands.command(name="case",)
    @commands.has_permissions(administrator=True)
    async def _case(self, ctx, id: int, *, reason):
        async with ctx.bot.pool.acquire() as conn:
            guild = await conn.fetchrow(
                "SELECT * FROM guilds WHERE id = $1", ctx.channel.guild.id
            )
            if guild["modlogs"]:
                modlogs = self.bot.get_channel(guild["modlogs"])

                try:
                    data = await conn.fetchrow(
                        "UPDATE infractions SET reason = $1 WHERE id = $2 AND guild = $3 RETURNING *",
                        reason,
                        id,
                        ctx.channel.guild.id,
                    )
                    modlogs_message = await modlogs.fetch_message(data["modlogs"])
                    role = ctx.guild.get_role(guild["muterole"])
                    user = await self.bot.fetch_user(data["target"])

                    await modlogs_message.edit(
                        content=dedent(
                            f"""
                    **{data['type']}** | Case {data['id']}
                    **User**: {user} ({user.id}) ({user.mention})
                    **Reason**: {reason}
                    **Responsible Moderator**: {ctx.author}
                    {f"**Role**: {role.name} ({role.id})" if data['type'] == "Mute" or "Unmute" else ""}
                    """
                        )
                    )
                except Exception as err:
                    return await ctx.channel.send(
                        f"Don't expect me to know what happened >:)\n{err}"
                    )

            await ctx.channel.send(f"👌")

    @commands.group(name="infractions", invoke_without_command=True)
    async def _infractions(self, ctx):
        return

    @_infractions.command(name="delete")
    @commands.has_permissions(administrator=True)
    async def _delete(self, ctx):

        try:
            await self.bot.pool.execute(
                "DELETE FROM infractions WHERE guild = $1", ctx.channel.guild.id
            )
            del self.bot.cases[ctx.channel.guild.id]
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(f"👌")

    @_infractions.command(name="archive")
    @commands.has_permissions(manage_guild=True)
    async def _archive(self, ctx):

        try:
            async with ctx.bot.pool.acquire() as conn:
                infractions = await conn.fetch(
                    "SELECT * FROM infractions WHERE guild = $1", ctx.channel.guild.id
                )

                if not infractions:
                    return await ctx.channel.send(
                        "Your server doesn't have any infractions smart guy"
                    )

                with open(
                    f"wrenchboat/assets/{ctx.guild.name}_{ctx.guild.id}.csv", "w+"
                ) as file:
                    filewriter = csv.writer(
                        file, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL
                    )

                    filewriter.writerow(
                        ["Moderator", "User", "Type", "Reason", "Time",]
                    )
                    for x in infractions:
                        moderator = ctx.channel.guild.get_member(x["moderator"])
                        user = await self.bot.fetch_user(x["target"])
                        try:
                            filewriter.writerow(
                                [
                                    f"{moderator} ({moderator.id})",
                                    f"{user} ({user.id})",
                                    x["type"],
                                    x["reason"],
                                    x["time_punsihed"],
                                ]
                            )
                        except:
                            continue

                file_object = open(
                    f"wrenchboat/assets/{ctx.guild.name}_{ctx.guild.id}.csv", "rb",
                )
                Archive = discord.File(
                    filename=f"{ctx.guild.name}_{ctx.guild.id}.csv", fp=file_object
                )
                await ctx.channel.send(
                    f"I have archived all moderative actions. You can download it I guess :|",
                    file=Archive,
                )
                file_object.close()
                os.remove(f"wrenchboat/assets/{ctx.guild.name}_{ctx.guild.id}.csv")

        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

    @commands.group(name="note", invoke_without_command=True)
    @commands.has_permissions(manage_messages=True)
    async def _note(
        self, ctx, user: discord.Member, *, reason,
    ):

        if not checks.above(self.bot, user, ctx.author):
            return

        try:
            await self.bot.pool.execute(
                f"INSERT INTO notes(guild,author,target,content,time_given) VALUES($1,$2,$3,$4,$5)",
                ctx.channel.guild.id,
                ctx.author.id,
                user.id,
                reason,
                datetime.utcnow(),
            )
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(f"📋")

    @_note.command(name="info")
    @commands.has_permissions(manage_messages=True)
    async def _note_info(self, ctx, id: int):

        async with ctx.bot.pool.acquire() as conn:

            selected = await conn.fetchrow("SELECT * FROM notes WHERE id = $1", id)

            try:
                await ctx.channel.send(
                    dedent(
                        f"""
                📋 **{selected['id']}**
                **User**: {await self.bot.fetch_user(selected['target'])} ({selected['target']}) (<@{selected['target']}>)
                **Moderator**: {await self.bot.fetch_user(selected['author'])}
                **Note**: {selected['content']}
                """
                    ),
                    allowed_mentions=discord.AllowedMentions(
                        everyone=False, roles=False, users=False
                    ),
                )
            except Exception as err:
                print(err)

    @_note.command(name="delete")
    @commands.has_permissions(manage_messages=True)
    async def _note_delete(self, ctx, id: int):

        async with ctx.bot.pool.acquire() as conn:
            try:
                await conn.fetchrow("DELETE FROM notes WHERE id = $1", id)
            except Exception as err:
                print(err)

            await ctx.channel.send(":ok_hand:")

    @_note.command(name="search")
    @commands.has_permissions(manage_messages=True)
    async def _note_search(self, ctx, user: discord.User):

        async with ctx.bot.pool.acquire() as conn:
            selected = await conn.fetch(
                "SELECT * FROM notes WHERE guild = $1 AND target = $2",
                ctx.channel.guild.id,
                user.id,
            )
            if not selected:
                return await ctx.channel.send("Nope! They are clean!!!!")
            list = ""

            try:
                for x in selected:
                    list += f"{x['id']}: {x['content']}"

                if len(list) > 1700:
                    await ctx.channel.send(f"""I am now showing you {user}'s notes!""")
                    for i in range(math.ceil(len(list) / 1992)):
                        chunk = list[(i - 1) * 1700 : i * 1992]
                        await ctx.channel.send(f"```\n{chunk}\n```")
                else:
                    await ctx.channel.send(
                        f"""I am now showing you {user}'s notes!```{list}```"""
                    )
            except Exception as err:
                print(err)


def setup(bot):
    bot.add_cog(moderation(bot))
