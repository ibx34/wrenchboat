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

seconds_per_unit = {"s": 1, "m": 60, "h": 3600}

def convert_to_seconds(s):
    return int(s[:-1]) * seconds_per_unit[s[-1]]

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
        name="setrole",
        usage="@user (role)",
        description="Add a role to a user on the fly. :warning: If the role you are trying to add is above you, it wont respond.",
    )
    @commands.has_permissions(manage_roles=True)
    async def _setrole(self, ctx, user: discord.Member, *, role: discord.Role):

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

    @commands.command(
        name="removerole",
        usage="@user (role)",
        description="Remove a role from a user on the fly. :warning: If the role you are trying to add is above you, it wont respond.",
    )
    @commands.has_permissions(manage_roles=True)
    async def _removerole(self, ctx, user: discord.Member, *, role: discord.Role):

        if checks.above(self=self.bot, user=user, moderator=ctx.author) is False:
            return await ctx.channel.send(
                f"You're literally an idiot. You don't have permission to do that. Did you think I was gonna let you?"
            )

        if checks.role_above(self=self.bot, user=ctx.author, role=role) is False:
            return  # await ctx.channel.send(f"You're literally an idiot. You don't have permission to do that. Did you think I was gonna let you?")

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

    @commands.command(
        name="decancer",
        usage="@user",
        description="Remove any non numeric or alphanumeric characters from a user's nickname or name",
    )
    @commands.has_permissions(manage_nicknames=True)
    async def _decancer(self, ctx, user: discord.Member):

        try:
            if user.nick.isalnum() == False or user.name.isalnum() == False:
                await user.edit(
                    nick="Decancered name",
                    reason=f"[{ctx.author}]: Decancer {user} ({user.id})",
                )

        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(f"I have decancered {user}'s nickname (or name).")
        await modlogs(
            self=self.bot,
            moderator=ctx.author,
            user=user,
            reason=f"Name decancer",
            type=ctx.command.name.capitalize(),
            case=None,
            time=datetime.utcnow(),
        )

    @commands.group(
        name="purge",
        invoke_without_command=True,
        usage="(amount)",
        description="Purge an amount of messages from a channel. (Pinned messages are ignored).",
    )
    @commands.has_permissions(manage_messages=True)
    async def _purge(self, ctx, amount: int):
        def is_pinned(m):
            return not m.pinned

        try:
            purged = await ctx.channel.purge(limit=amount, check=is_pinned)
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
            purged = await ctx.channel.purge(limit=amount, check=is_x)
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
            purged = await ctx.channel.purge(limit=amount, check=is_bot)
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
            purged = await ctx.channel.purge(limit=amount, check=has_embed)
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
            purged = await ctx.channel.purge(limit=int(amount), check=contains_x)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"I have purged **{len(purged)}** messages that contained `{contains}`. *I'm serious this one took a lot to do, thank me*"
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

    @commands.command(name="clearvoice",usage="(voice channel id)",description="Clear a voice channel of all users. :) very useful for voice raids")
    @commands.has_permissions(manage_channels=True)
    async def _clearvoice(self,ctx,*,voice:discord.VoiceChannel=None):
        try:
            if voice is None:
                voice = ctx.author.voice.channel

            count = 0
            list = []
            for x in voice.voice_states:
                member = ctx.channel.guild.get_member(x)
                await member.move_to(None,reason=f"[ {ctx.author} ] cleared voice channel: {voice.name}")
                count += 1
                list.append(member.mention)
        except Exception as err:
            return await ctx.channel.send(f"Don't expect me to know what happened >:)\n{err}")        

        await ctx.channel.send(f"I have cleared voice channel: **{voice.name}**, thank me!!!!\n**Stats**:\nUsers removed: {count}\nUsers: {', '.join(list)}",
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, users=False
            )
        )
    
    @commands.command(name="clearreactions",usage="(message id)",description="Clear a message of a reaction. Could be useful if you want to get a message cleaned.")#,invoke_without_command=True)
    @commands.has_permissions(manage_messages=True)
    async def _clearreactions(self,ctx,message:discord.Message):

        emojis = {}
        try:
            for x in message.reactions:
                emojis[x.emoji] = x.count
            await message.clear_reactions()
        except Exception as err:
            return await ctx.channel.send(f"Don't expect me to know what happened >:)\n{err}")        
        
        list = [f"{x}**count**: `{emojis[x]}`" for x in emojis]
        await ctx.channel.send(f"I have cleared the message of **all** reactions.\n**Stats**:\n{', '.join(list)}")
    
    @commands.group(name="slowmode", usage="(time)", description="Set a channel's slowmod on the fly. *Be like sonic and zoommmmmm*",invoke_without_command=True)
    @commands.has_permissions(manage_channels=True)
    async def _slowmode(self,ctx,time):

        if convert_to_seconds(time) > 21600:
            return await ctx.channel.send("Ight home boy, ima tell ya something. That is not possible... (You can't set a slowmode over 6 hours)")

        try:
            await ctx.channel.edit(slowmode_delay=convert_to_seconds(time))
        except Exception as err:
            return await ctx.channel.send(f"Don't expect me to know what happened >:)\n{err}")       
        
        return await ctx.channel.send(f"Okay? I set {ctx.channel.mention}'s slowmode to {time}..")

    @_slowmode.command(name="remove", usage="None", description="Remove a slowmode from a channel. Of course **on the fly**")
    @commands.has_permissions(manage_channels=True)
    async def _remove(self,ctx):    

        try:
            await ctx.channel.edit(slowmode_delay=None)
        except Exception as err:
            return await ctx.channel.send(f"Don't expect me to know what happened >:)\n{err}")       
        
        return await ctx.channel.send(f"👍")    

    @commands.command(name="clearinvites",usage="<amount of uses>",description="Clear your server's invites based on uses.")    
    @commands.has_permissions(administrator=True)
    async def _clearinvites(self,ctx,usess:int):

        try:
            invites = {}
            for x in await ctx.guild.invites():
                if x.uses < usess:
                    invites[x.code] = x.uses
                    await x.delete(reason=f"[ Invite Purge ]: use count under {usess}")
        except Exception as err:
            return await ctx.channel.send(f"Don't expect me to know what happened >:)\n{err}")       
        
        list = [f"**{x}**: {invites[x]}" for x in invites]
        return await ctx.channel.send(f"👌\n**Stats**:\n{', '.join(list)}")                        

def setup(bot):
    bot.add_cog(admin(bot))
