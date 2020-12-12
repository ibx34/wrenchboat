import csv
import json
import os
import random
import re
import sys
import typing
from datetime import datetime, timedelta
from itertools import accumulate
from textwrap import dedent

import aiohttp
import aioredis
import arrow
import asyncpg
import config
import discord
import yaml
from discord.ext import commands
from unidecode import unidecode

from wrenchboat.utils import pagination
from wrenchboat.utils.checks import checks
from wrenchboat.utils.modlogs import modlogs

seconds_per_unit = {"s": 1, "m": 60, "h": 3600}


def convert_to_seconds(s):
    return int(s[:-1]) * seconds_per_unit[s[-1]]


def left_pad(string: str, amount: int) -> str:
    return " " * (amount - len(string)) + string


class admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="nick",
        usage="@user <nickname>",
        description="Set a user's nickname. (If nickname is empty the bot will set their name back to normal).",
    )
    @commands.has_permissions(manage_nicknames=True)
    async def _nick(self, ctx, user: discord.Member, *, new_nick: str = None):

        try:
            if new_nick is not None:
                if len(new_nick) > 30:
                    return
            await user.edit(
                nick=new_nick or user.name,
                reason=f"[{ctx.author}]: Nicked {user} ({user.id})",
            )

        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"I have nicked {user}. (Their nickname is now `{new_nick or 'their normal name'}`)."
        )

    @commands.command(
        name="dezalgo",
        usage="@user",
        description="Removes and trys to translate any zalgo in a users nickname",
    )
    @commands.has_permissions(manage_nicknames=True)
    async def _dezalgo(self, ctx, user: discord.Member, *, new_nick: str = None):

        try:
            await user.edit(
                nick="".join(filter(str.isalnum, user.nick[:32])),
                reason=f"[{ctx.author}]: dezalgo {user} ({user.id})",
            )
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f":ok_hand: I removed any zalgo that I found. Their new nick is `{user.nick}`"
        )

    @commands.command(
        name="decancer",
        usage="@user",
        description="Remove any annoying / spammy characters from a users nickname (or name)",
    )
    @commands.has_permissions(manage_nicknames=True)
    async def _decancer(self, ctx, user: discord.Member):

        try:
            new_name = unidecode(user.nick) if user.nick else unidecode(user.name)
            await user.edit(
                nick=new_name[:32], reason=f"[{ctx.author}]: Decancer {user} ({user.id})",
            )

        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"I have cleaned {user}!!!!!! Their new nickname is `{new_name}`"
        )

    @commands.command(
        name="dehoist",
        usage="@user",
        description="Remove an characters in a user's name that may allow them to hoist.",
    )
    @commands.has_permissions(manage_nicknames=True)
    async def _dehoist(self, ctx, user: discord.Member):

        try:
            for x in config.characters:
                if user.nick.startswith(x):
                    await user.edit(
                        nick=" ឵" + user.nick.replace(x, ""),
                        reason=f"[{ctx.author}]: Name sanitation",
                    )
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"I have dehoisted {user}. Their new nickname is `{user.nick}`"
        )

    @commands.group(
        name="archive",
        usage="<amount>",
        description="Archive a channel to a CSV file.",
        invoke_without_command=True,
    )
    @commands.has_permissions(manage_messages=True)
    async def _archive(self, ctx, amount: int = None):

        try:
            messages = await ctx.channel.history(
                limit=amount, oldest_first=True
            ).flatten()
            with open(
                f"wrenchboat/assets/{ctx.channel.name}_{ctx.channel.id}.csv", "w+"
            ) as file:
                filewriter = csv.writer(
                    file, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL
                )

                filewriter.writerow(
                    [
                        "Author",
                        "Author's Id",
                        "Message Created",
                        "Message Created (Humanized)",
                        "Message Content",
                    ]
                )
                for x in messages:
                    try:
                        filewriter.writerow(
                            [
                                x.author,
                                f"{x.author.id}",
                                x.created_at,
                                arrow.get(x.created_at).humanize(),
                                x.content,
                            ]
                        )
                    except:
                        continue

            file_object = open(
                f"wrenchboat/assets/{ctx.channel.name}_{ctx.channel.id}.csv", "rb",
            )
            Archive = discord.File(
                filename=f"{ctx.channel.name}_{ctx.channel.id}.csv", fp=file_object
            )
            await ctx.channel.send(
                f"I did what you wanted, now take the file. (I have archived {ctx.channel.mention}).",
                file=Archive,
            )
            file_object.close()
            os.remove(f"wrenchboat/assets/{ctx.channel.name}_{ctx.channel.id}.csv")
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

    @_archive.command(
        name="from",
        usage="@user <amount>",
        description="Archive either all or a certain amount of messages from a user",
    )
    @commands.has_permissions(manage_messages=True)
    async def _archive_from(self, ctx, user: discord.Member, amount: int = None):

        try:
            messages = await ctx.channel.history(
                limit=amount, oldest_first=True
            ).flatten()
            with open(f"wrenchboat/assets/{user.name}_{user.id}.csv", "w+") as file:
                filewriter = csv.writer(
                    file, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL
                )

                filewriter.writerow(
                    [
                        "Author",
                        "Author's Id",
                        "Message Created",
                        "Message Created (Humanized)",
                        "Message Content",
                    ]
                )
                for x in messages:
                    if x.author != user:
                        continue
                    try:
                        filewriter.writerow(
                            [
                                x.author,
                                f"{x.author.id}",
                                x.created_at,
                                arrow.get(x.created_at).humanize(),
                                x.content,
                            ]
                        )
                    except:
                        continue

            file_object = open(f"wrenchboat/assets/{user.name}_{user.id}.csv", "rb",)
            Archive = discord.File(
                filename=f"{user.name}_{user.id}.csv", fp=file_object
            )
            await ctx.channel.send(
                f"I did what you wanted, now take the file. (I have archived messages from {user}).",
                file=Archive,
            )
            file_object.close()
            os.remove(f"wrenchboat/assets/{user.name}_{user.id}.csv")
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

    @_archive.command(
        name="in",
        usage="#channel <amount>",
        description="Archive either all or a certain amount of messages in a channel",
    )
    @commands.has_permissions(manage_messages=True)
    async def _archive_in(self, ctx, channel: discord.TextChannel, amount: int = None):

        try:
            messages = await channel.history(limit=amount, oldest_first=True).flatten()
            with open(
                f"wrenchboat/assets/{channel.name}_{channel.id}.csv", "w+"
            ) as file:
                filewriter = csv.writer(
                    file, delimiter=",", quotechar="|", quoting=csv.QUOTE_MINIMAL
                )

                filewriter.writerow(
                    [
                        "Author",
                        "Author's Id",
                        "Message Created",
                        "Message Created (Humanized)",
                        "Message Content",
                    ]
                )
                for x in messages:
                    try:
                        filewriter.writerow(
                            [
                                x.author,
                                f"{x.author.id}",
                                x.created_at,
                                arrow.get(x.created_at).humanize(),
                                x.content,
                            ]
                        )
                    except:
                        continue

            file_object = open(
                f"wrenchboat/assets/{channel.name}_{channel.id}.csv", "rb",
            )
            Archive = discord.File(
                filename=f"{channel.name}_{channel.id}.csv", fp=file_object
            )
            await ctx.channel.send(
                f"I did what you wanted, now take the file. (I have archived messages in {channel.mention}).",
                file=Archive,
            )
            file_object.close()
            os.remove(f"wrenchboat/assets/{channel.name}_{channel.id}.csv")
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

    @commands.command(
        name="clearvoice",
        usage="(voice channel id)",
        description="Clear a voice channel of all users. :) very useful for voice raids",
    )
    @commands.has_permissions(manage_channels=True)
    async def _clearvoice(self, ctx, *, voice: discord.VoiceChannel = None):
        try:
            if voice is None:
                voice = ctx.author.voice.channel

            count = 0
            list = []
            for x in voice.voice_states:
                member = ctx.channel.guild.get_member(x)
                await member.move_to(
                    None, reason=f"[ {ctx.author} ] cleared voice channel: {voice.name}"
                )
                count += 1
                list.append(member.mention)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"I have cleared voice channel: **{voice.name}**, thank me!!!!\n**Stats**:\nUsers removed: {count}\nUsers: {', '.join(list)}",
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, users=False
            ),
        )

    @commands.command(
        name="clearreactions",
        usage="(message id)",
        description="Clear a message of a reaction. Could be useful if you want to get a message cleaned.",
    )  # ,invoke_without_command=True)
    @commands.has_permissions(manage_messages=True)
    async def _clearreactions(self, ctx, message: discord.Message):

        emojis = {}
        try:
            for x in message.reactions:
                emojis[x.emoji] = x.count
            await message.clear_reactions()
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        list = [f"{x}**count**: `{emojis[x]}`" for x in emojis]
        await ctx.channel.send(
            f"I have cleared the message of **all** reactions.\n**Stats**:\n{', '.join(list)}"
        )

    @commands.group(
        name="slowmode",
        usage="(time)",
        description="Set a channel's slowmode on the fly. *Be like sonic and zoommmmmm*",
        invoke_without_command=True,
    )
    @commands.has_permissions(manage_channels=True)
    async def _slowmode(self, ctx, time):

        if convert_to_seconds(time) > 21600:
            return await ctx.channel.send(
                "Ight home boy, ima tell ya something. That is not possible... (You can't set a slowmode over 6 hours)"
            )

        try:
            await ctx.channel.edit(slowmode_delay=convert_to_seconds(time))
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        return await ctx.channel.send(
            f"Okay? I set {ctx.channel.mention}'s slowmode to {time}.."
        )

    @_slowmode.command(
        name="remove",
        usage="None",
        description="Remove a slowmode from a channel. Of course **on the fly**",
    )
    @commands.has_permissions(manage_channels=True)
    async def _remove(self, ctx):

        try:
            await ctx.channel.edit(slowmode_delay=None)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        return await ctx.channel.send(f"👍")

    @commands.command(
        name="clearinvites",
        usage="<amount of uses>",
        description="Clear your server's invites based on uses.",
    )
    @commands.has_permissions(administrator=True)
    async def _clearinvites(self, ctx, usess: int):

        try:
            invites = {}
            for x in await ctx.guild.invites():
                if x.uses < usess:
                    invites[x.code] = x.uses
                    await x.delete(reason=f"[ Invite Purge ]: use count under {usess}")
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        list = [f"**{x}**: {invites[x]}" for x in invites]
        return await ctx.channel.send(f"👌\n**Stats**:\n{', '.join(list)}")

    @commands.command(
        name="post",
        usage="#channel @role <message>",
        description="Send a message to a channel that pings a role. Gotta be sneky",
    )
    @commands.has_permissions(administrator=True)
    async def _post(
        self, ctx, channel: discord.TextChannel, role: discord.Role, *, message
    ):

        try:
            await channel.send(
                f"{role.mention}\n\n{message}\n\n*Message by: {ctx.author}*"
            )
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(":ok_hand:")

    @commands.group(
        name="role",
        invoke_without_command=True,
        description="Manage your server's roles with my many commands :)",
        aliases=["roles"],
    )
    @commands.has_permissions(manage_roles=True)
    async def _role(self, ctx):

        list = []
        length = [round(len(ctx.channel.guild.roles) / 1)]
        pages = []
        for x in ctx.channel.guild.roles:
            list.append(f"**{x.mention}**: `{x.id}`")

        Output = [list[x - y : x] for x, y in zip(accumulate(length), length)]

        for x in Output:
            embed = discord.Embed(color=0x99AAB5, description="\n ".join(x))
            pages.append(embed)

        paginator = pagination.BotEmbedPaginator(ctx, pages)
        return await paginator.run()

    @_role.command(
        name="add",
        usage="@user (role)",
        description="Add a role to a user on the fly. If the role you are trying to add is above you, it wont respond.",
    )
    @commands.has_permissions(manage_roles=True)
    async def _add(self, ctx, user: discord.Member, *, role: discord.Role):

        if checks.above(self=self.bot, user=user, moderator=ctx.author) is False:
            return await ctx.channel.send(
                f"You're literally an idiot. You don't have permission to do that. Did you think I was gonna let you?"
            )

        if checks.role_above(self=self.bot, user=ctx.author, role=role) is False:
            return

        try:
            await user.add_roles(role)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"Okay, I added the role {role.mention} to {user}, happy?",
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, users=False
            ),
        )

    @_role.command(
        name="remove",
        usage="@user (role)",
        description="Remove a role from a user on the fly. If the role you are trying to add is above you, it wont respond.",
    )
    @commands.has_permissions(manage_roles=True)
    async def _role_remove(self, ctx, user: discord.Member, *, role: discord.Role):

        if checks.above(self=self.bot, user=user, moderator=ctx.author) is False:
            return await ctx.channel.send(
                f"You're literally an idiot. You don't have permission to do that. Did you think I was gonna let you?"
            )

        if checks.role_above(self=self.bot, user=ctx.author, role=role) is False:
            return

        try:
            await user.remove_roles(role)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"Okay, I removed the role {role.mention} from {user}, happy?",
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, users=False
            ),
        )

    @_role.command(
        name="all",
        usage="@role",
        description="Add a role to all users in your server. *May take some time.*",
    )
    @commands.has_permissions(administrator=True)
    async def _all(self, ctx, role: discord.Role):

        try:
            count = 0
            for x in ctx.guild.members:
                await x.add_roles(role)
                count += 1
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"👌 I have added {role.mention} to {count} users.",
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, users=False
            ),
        )

    @_role.command(
        name="nuke",
        usage="@role",
        description="Remove a role from everyone **WITH** the role.",
    )
    @commands.has_permissions(administrator=True)
    async def _nuke(self, ctx, role: discord.Role):

        try:
            count = 0
            for x in role.members:
                await x.remove_roles(role)
                count += 1
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"👌 I have removed {role.mention} from {count} users.",
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, users=False
            ),
        )

    @_role.command(
        name="create",
        usage="(name)",
        description="Create a role on your server, great for lazy people",
    )
    @commands.has_permissions(administrator=True)
    async def _create(self, ctx, *, name: str):
        if len(name) > 30:
            return await ctx.channel.send(
                "Okay smart guy, want me to get introuble? Your names cant be over **30** characters"
            )

        try:
            await ctx.guild.create_role(
                name=name, reason=f"Role create by {ctx.author}"
            )
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(":ok_hand:")

    @_role.command(
        name="delete",
        usage="@role",
        description="Swiftly delete a role from your server!!!!!",
    )
    @commands.has_permissions(administrator=True)
    async def _delete(self, ctx, *, role: discord.Role):

        try:
            await role.delete(reason=f"Role deleted by {ctx.author}")
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(":ok_hand:")

    @_role.command(name="id", usage="@role", description="Get the id of a role")
    async def _id(self, ctx, *, role: discord.Role):

        try:
            await ctx.channel.send(
                f"**{role.mention}'s** id is `{role.id}`",
                allowed_mentions=discord.AllowedMentions(
                    everyone=False, roles=False, users=False
                ),
            )

        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

    @_role.command(name="color", usage="@role", description="Get the color of a role")
    async def _color(self, ctx, *, role):

        try:
            await ctx.channel.send(
                f"**{role.mention}'s** color is `{role.color}`",
                allowed_mentions=discord.AllowedMentions(
                    everyone=False, roles=False, users=False
                ),
            )
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

    @_role.command(
        name="memberids",
        usage="@role",
        description="Get all member's ids who are in a role.",
        aliases=["roleids"],
    )
    @commands.has_permissions(administrator=True)
    async def _memberids(self, ctx, *, role: discord.Role):

        list = []
        length = [round(len(role.members) / 1)]
        pages = []
        for x in role.members:
            list.append(f"**{x.mention}**: `{x.id}`")

        Output = [list[x - y : x] for x, y in zip(accumulate(length), length)]

        for x in Output:
            embed = discord.Embed(color=0x99AAB5, description="\n ".join(x))
            pages.append(embed)

        paginator = pagination.BotEmbedPaginator(ctx, pages)
        return await paginator.run()

    @commands.group(
        name="channel",
        description="Manage your server's channels with cool :sunglasses: options",
        invoke_without_command=True,
    )
    @commands.has_permissions(manage_channels=True)
    async def _channel(self, ctx):
        return

    @_channel.command(
        name="lock",
        usage="<channel>",
        description="Lock a channel so users can't speak in it.",
    )
    @commands.has_permissions(manage_channels=True)
    async def _lock(self, ctx, *, channel: discord.TextChannel = None):

        if channel is None:
            channel = ctx.channel

        perms = channel.overwrites_for(ctx.guild.default_role)
        perms.send_messages = False

        try:
            await channel.set_permissions(
                ctx.guild.default_role,
                overwrite=perms,
                reason=f"[{ctx.author}]: channel lock ({channel.name})",
            )
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send("🔒 channel locked!")

    @_channel.command(
        name="unlock",
        usage="<channel>",
        description="These will revert changes from lock. Make sure that the role has send messages otherwise this wont change anything",
    )
    @commands.has_permissions(manage_channels=True)
    async def _unlock(self, ctx, *, channel: discord.TextChannel = None):

        if channel is None:
            channel = ctx.channel

        perms = channel.overwrites_for(ctx.guild.default_role)
        perms.send_messages = None

        try:
            await channel.set_permissions(
                ctx.guild.default_role,
                overwrite=perms,
                reason=f"[{ctx.author}]: channel unlock ({channel.name})",
            )
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send("🔓 channel unlocked!")

    @_channel.command(
        name="voicelock",
        usage="<channel>",
        description="Lock a channel so users can't speak in it.",
    )
    @commands.has_permissions(manage_channels=True)
    async def _voicelock(self, ctx, *, channel: discord.VoiceChannel = None):

        if channel is None:
            channel = ctx.channel

        perms = channel.overwrites_for(ctx.guild.default_role)
        perms.connect = False

        try:
            await channel.set_permissions(
                ctx.guild.default_role,
                overwrite=perms,
                reason=f"[{ctx.author}]: voice channel lock ({channel.name})",
            )
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send("🔈🔒 channel locked!")

    @_channel.command(
        name="voiceunlock",
        usage="<channel>",
        description="Allow users back into a previously locked voice channel.",
    )
    @commands.has_permissions(manage_channels=True)
    async def _voiceunlock(self, ctx, *, channel: discord.VoiceChannel = None):

        if channel is None:
            channel = ctx.channel

        perms = channel.overwrites_for(ctx.guild.default_role)
        perms.connect = None

        try:
            await channel.set_permissions(
                ctx.guild.default_role,
                overwrite=perms,
                reason=f"[{ctx.author}]: voice channel unlock ({channel.name})",
            )
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send("🔊🔓 channel unlocked!")

    @_channel.command(
        name="hide",
        usage="<channel>",
        description="Hide a channel from `@everyone`'s peeping eyes :eyes:",
    )
    @commands.has_permissions(manage_channels=True)
    async def _hide(self, ctx, *, channel: discord.TextChannel = None):

        if channel is None:
            channel = ctx.channel

        perms = channel.overwrites_for(ctx.guild.default_role)
        perms.view_channel = False

        try:
            await channel.set_permissions(
                ctx.guild.default_role,
                overwrite=perms,
                reason=f"[{ctx.author}]: channel hide ({channel.name})",
            )
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            "👀 channel now hidden! *If the user was viewing the channel while you ran the command they can still see it*"
        )

    @_channel.command(
        name="unhide",
        usage="<channel>",
        description="Give `@everyone` permission to see the channel again like a good owner",
    )
    @commands.has_permissions(manage_channels=True)
    async def _unhide(self, ctx, *, channel: discord.TextChannel = None):

        if channel is None:
            channel = ctx.channel

        perms = channel.overwrites_for(ctx.guild.default_role)
        perms.view_channel = None

        try:
            await channel.set_permissions(
                ctx.guild.default_role,
                overwrite=perms,
                reason=f"[{ctx.author}]: channel hide ({channel.name})",
            )
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send("👀 channel now visible!")

    @_channel.command(
        name="voicehide",
        usage="<channel>",
        description="Hide a channel from `@everyone`'s peeping eyes :eyes: **(Voice Edition)**",
    )
    @commands.has_permissions(manage_channels=True)
    async def _voicehide(self, ctx, *, channel: discord.VoiceChannel = None):

        if channel is None:
            channel = ctx.channel

        perms = channel.overwrites_for(ctx.guild.default_role)
        perms.view_channel = False

        try:
            await channel.set_permissions(
                ctx.guild.default_role,
                overwrite=perms,
                reason=f"[{ctx.author}]: channel hide ({channel.name})",
            )
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            "👀 channel now hidden! *If the user was in the channel while it was being hidden they can stil see it.*"
        )

    @_channel.command(
        name="voiceunhide",
        usage="<channel>",
        description="Give `@everyone` permission to see the channel again like a good owner **(Voice Edition)**",
    )
    @commands.has_permissions(manage_channels=True)
    async def _voiceunhide(self, ctx, *, channel: discord.VoiceChannel):

        if channel is None:
            channel = ctx.channel

        perms = channel.overwrites_for(ctx.guild.default_role)
        perms.view_channel = None

        try:
            await channel.set_permissions(
                ctx.guild.default_role,
                overwrite=perms,
                reason=f"[{ctx.author}]: channel hide ({channel.name})",
            )
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send("👀 channel now visible!")

    @commands.group(
        name="noroles", description="View my commands for more info you cutie <3"
    )
    async def _noroles(self, ctx):
        return

    @_noroles.command(
        name="show", description="Shows all users without a role in your server"
    )
    @commands.has_permissions(manage_roles=True)
    async def _noroles_show(self, ctx):

        list = []
        for x in ctx.guild.members:
            if x.roles == [ctx.guild.default_role]:
                list.append(x)
        length = [round(len(list) / 1)]
        pages = []

        Output = [list[x - y : x] for x, y in zip(accumulate(length), length)]

        for x in Output:
            embed = discord.Embed(
                color=0x99AAB5,
                description="\n ".join(f"**{x.mention}**: `{x.id}`" for x in x),
            )
            pages.append(embed)

        paginator = pagination.BotEmbedPaginator(ctx, pages)
        return await paginator.run()

    @_noroles.command(
        name="prune", description="Removes all users from your server with no role."
    )
    @commands.has_permissions(manage_roles=True)
    async def _noroles_prune(self, ctx):

        list = []
        for x in ctx.guild.members:
            if x.roles == [ctx.guild.default_role]:
                list.append(x)

        for x in list:
            try:
                await x.kick(reason=f"Auto kick: User has no roles.")
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

        await ctx.channel.send(
            f":ok_hand: {len(list)} users have been kicked!\n**Users kicked:**\n{', '.join(f'{x}' for x in list)}"
        )

    @commands.command(name="config", description="Check your server's config.")
    @commands.has_permissions(manage_guild=True)
    async def _config(self, ctx):
        async with self.bot.pool.acquire() as conn:
            guild = await conn.fetchrow(
                "SELECT * FROM guilds WHERE id = $1", ctx.channel.guild.id
            )

            await ctx.channel.send(
                dedent(
                    f"""
            ```json
            {{
                "config": {{              
                    "prefixes": "{', '.join(guild['prefixes'])}",
                    "archive category": {guild['archive_category']}, 
                    "server language": {guild['language']},
                    "response type": {guild['response_type']},
                    "global bans": {guild['global_bans']},
                    "moderation": {{
                        "moderator role": {guild['modrole']},
                        "don't mute role": {guild['dontmute']},
                        "muted role": {guild['muterole']},
                    }},
                    "auto-moderation": {{
                        "anti profanity": {f"{guild['antiprofanity']}" if guild['antiprofanity'] else "False"},
                        "anti hoisting": {guild['antihoist']},
                        "anti invite": {f"{guild['antinvite']}" if guild['antinvite'] else "False"},
                        "anti massping": {f"{guild['antimassping']}" if guild['antimassping'] else "False"},
                        "token remover": {guild['token_remover']}
                    }},
                    "logging": {{
                        "mod logs": {guild['modlogs']},
                        "message logs": {guild['messagelogs']},
                        "automod logs": {guild['automodlogs']},
                        "user logs": {guild['userlogs']},
                        "server logs": {guild['serverlogs']},
                    }},
                    "starboard": {{
                        "self starring": {guild['self_starring']},
                        "needed stars": {guild['needed_stars']},
                        "starboard channel": {guild['starboard_channel']}
                    }}
                }}
            }}
            ```
            """
                )
            )

    @commands.command(
        name="archivem",
        usage="<#channel>",
        description="Archive a channel and move it to your server's archive category",
    )
    @commands.has_permissions(manage_channels=True)
    async def _archivem(
        self,
        ctx,
        channel: typing.Union[discord.TextChannel, discord.VoiceChannel],
        *,
        reason=None,
    ):
        async with self.bot.pool.acquire() as conn:
            guild = await conn.fetchrow("SELECT * FROM guilds WHERE id = $1", ctx.channel.guild.id)
            archives = await conn.fetchrow("SELECT * FROM archived_channels WHERE channel = $1", channel.id)

            if archives:
                return await ctx.channel.send("Stop 🛑 That channel is already archived!")

            if not guild["archive_category"]:
                return await ctx.channel.send(
                    f"On no! Where do I send the channel to? Run `{ctx.prefix}archivecategory <category id>` so I know where to send it!!!"
                )
            

            try:
                await conn.execute(
                    "INSERT INTO archived_channels(category,channel,position) VALUES($1,$2,$3)",
                    channel.category_id,
                    channel.id,
                    channel.position,
                )
                await channel.edit(
                    category=ctx.guild.get_channel(guild["archive_category"]),
                    reason=f"[ Channel Archive by {ctx.author} ] {reason}",
                )
                if channel.type == discord.ChannelType.text:
                    await channel.send(
                        embed=discord.Embed(
                            description=f"""Channel archived by {ctx.author}\n\n{f"{reason[:1900]}" if reason is not None else ""}""",
                            timestamp=datetime.utcnow(),
                        )
                    )

            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )
            await ctx.channel.send(f"Ok I have archived {channel.mention}!!!!!!")

    @commands.command(name="returnc",usage="<#channel>",description="Return a previously archived channel to its original posistion. :warning: If the category is was in was deleted the channel will will be put in not category.")
    @commands.has_permissions(manage_channels=True)
    async def _returnc(self,ctx,channel: typing.Union[discord.TextChannel, discord.VoiceChannel],*,reason=None,):    
        async with self.bot.pool.acquire() as conn:
            archived_channel = await conn.fetchrow("SELECT * FROM archived_channels WHERE channel = $1",channel.id)

            if not archived_channel:
                return await ctx.channel.send("Stop 🛑 That channel is **not** archived!! What are you thinking????")
            
            try:
                await channel.edit(category=ctx.guild.get_channel(archived_channel['category']),position=archived_channel['position'])
                await conn.execute("DELETE FROM archived_channels WHERE id = $1",archived_channel['id'])
            except Exception as err:
                return await ctx.channel.send(
                    f"Don't expect me to know what happened >:)\n{err}"
                )

            await ctx.channel.send(f"{channel.mention} has been returned to its rightful place!")

def setup(bot):
    bot.add_cog(admin(bot))
