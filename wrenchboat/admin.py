import csv
import os
import random
import re
import sys
from datetime import datetime
from itertools import accumulate
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
        aliases=['prune','clear','massdelete']
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

    @_purge.command(
        name="reactions",
        usage="(amount) <reation>",
        description="Purge an amount of messages that have reactions or a certain reaction.",
    )
    @commands.has_permissions(manage_messages=True)
    async def _reactions(self, ctx, amount: int, reaction:str=None):
        def has_reactions(m):
            if reaction is not None:
                for x in m.reactions:
                    if str(x) == reaction:
                        return x
            else:
                return m.reactions

        try:
            purged = await ctx.channel.purge(limit=int(amount), check=has_reactions)
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
    async def _mentions(self, ctx, amount: int, member:discord.Member=None):
        def has_mentions(m):
            if member is not None:
                if member.id in m.mentions.id:
                    return member
            else:
                return m.mentions

        try:
            purged = await ctx.channel.purge(limit=int(amount), check=has_mentions)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"I have purged **{len(purged)}** messages that {f'mentioned {member.mention} *no I didnt ping them <3*' if member is not None else 'had mentions in them'}",
            allowed_mentions=discord.AllowedMentions(
                everyone=False, users=False
            ),
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
            purged = await ctx.channel.purge(limit=int(amount), check=is_upper)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"I have purged **{len(purged)}** messages that had all caps in it.")

    @_purge.command(
        name="between",
        usage="(id 1) (id 2)",
        description="Purge an amount of messages that is between message **1** and message **2**",
    )
    @commands.has_permissions(manage_messages=True)
    async def _between(self, ctx, message1:discord.Message,message2:discord.Message):
        try:
            purged = await ctx.channel.purge(before=message2,after=message1)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"I have purged **{len(purged)}** messages that were between {message1.id} and {message2.id}")


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
        description="Send a message to a channel that pings a role. Gotta be sneky"
    )
    @commands.has_permissions(administrator=True)
    async def _post(self,ctx,channel:discord.TextChannel,role:discord.Role,*,message):

        try:
            await channel.send(f"{role.mention}\n\n{message}\n\n*Message by: {ctx.author}*")
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(":ok_hand:")

    @commands.group(name="role",invoke_without_command=True,description="Manage your server's roles with my many commands :)")
    async def _role(self,ctx):
        return

    @_role.command(name="add",
        usage="@user (role)",
        description="Add a role to a user on the fly. If the role you are trying to add is above you, it wont respond.",
    )
    @commands.has_permissions(manage_roles=True)
    async def _add(self, ctx, user: discord.Member, *, role:discord.Role):

        if checks.above(self=self.bot, user=user, moderator=ctx.author) is False:
            return await ctx.channel.send(
                f"You're literally an idiot. You don't have permission to do that. Did you think I was gonna let you?"
            )

        if checks.role_above(self=self.bot, user=ctx.author, role=role1) is False:
            return

        try:
            await user.add_roles(role1)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"Okay, I added the role {role1.mention} to {user}, happy?",
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
    async def _remove(self, ctx, user: discord.Member, *, role:discord.Role):



        if checks.above(self=self.bot, user=user, moderator=ctx.author) is False:
            return await ctx.channel.send(
                f"You're literally an idiot. You don't have permission to do that. Did you think I was gonna let you?"
            )

        if checks.role_above(self=self.bot, user=ctx.author, role=role1) is False:
            return

        try:
            await user.remove_roles(role1)
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"Okay, I removed the role {role1.mention} from {user}, happy?",
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, users=False
            )
        )

    @_role.command(
        name="all",
        usage="@role",
        description="Add a role to all users in your server. *May take some time.*",
    )
    @commands.has_permissions(administrator=True)
    async def _all(self, ctx, role:discord.Role):



        try:
            count = 0
            for x in ctx.guild.members:
                await x.add_roles(role1)
                count += 1
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"👌 I have added {role1.mention} to {count} users.",
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
    async def _nuke(self, ctx, role:discord.Role):



        try:
            count = 0
            for x in role1.members:
                await x.remove_roles(role1)
                count += 1
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(
            f"👌 I have removed {role1.mention} from {count} users.",
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, users=False
            ),
        )
    
    @_role.command(name="create",usage="(name)",description="Create a role on your server, great for lazy people")
    @commands.has_permissions(administrator=True)
    async def _create(self, ctx, *, name:str):    
        if len(name) > 30:
            return await ctx.channel.send("Okay smart guy, want me to get introuble? Your names cant be over **30** characters")

        try:
            await ctx.guild.create_role(name=name,reason=f"Role create by {ctx.author}")
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(":ok_hand:")

    @_role.command(name="delete",usage="@role",description="Swiftly delete a role from your server!!!!!")
    @commands.has_permissions(administrator=True)
    async def _delete(self, ctx, *, role:discord.Role):    



        try:
            await role1.delete(reason=f"Role deleted by {ctx.author}")
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )

        await ctx.channel.send(":ok_hand:")

    @_role.command(name="id",usage="@role",description="Get the id of a role")
    async def _id(self, ctx, *, role:discord.Role): 



        try:   
            await ctx.channel.send(f"**{role1.mention}'s** id is `{role1.id}`",
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, users=False
            ),
        )
    
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )
    
    @_role.command(name="color",usage="@role",description="Get the color of a role")
    async def _color(self, ctx, *, role): 

        try:   
            await ctx.channel.send(f"**{role1.mention}'s** color is `{role1.color}`",
            allowed_mentions=discord.AllowedMentions(
                everyone=False, roles=False, users=False
            ),
        )
        except Exception as err:
            return await ctx.channel.send(
                f"Don't expect me to know what happened >:)\n{err}"
            )    
    
    @_role.command(name="memberids",usage="@role",description="Get all member's ids who are in a role.",aliases=['roleids'])
    @commands.has_permissions(administrator=True)
    async def _memberids(self, ctx, *, role:discord.Role):     
        
        list = []
        length = [round(len(role1.members) / 1)]
        pages = []
        for x in role1.members:
            list.append(f"**{x.mention}**: `{x.id}`")    

        Output = [list[x - y: x] for x, y in zip(accumulate(length), length)]         
        
        for x in Output:
            embed = discord.Embed(color=0x99AAB5,description='\n '.join(x))
            pages.append(embed)
        
        paginator = pagination.BotEmbedPaginator(ctx, pages)
        return await paginator.run()        

    @commands.group(name="channel",description="Manage your server's channels with cool :sunglasses: options",invoke_without_command=True)
    @commands.has_permissions(manage_channels=True)
    async def _channel(self,ctx):
        return

    @_channel.command(name="lock",usage="<channel>",description="Lock a channel so users can't speak in it.")
    @commands.has_permissions(manage_channels=True)
    async def _lock(self, ctx, *,channel:discord.TextChannel=None):    

        if channel is None:
            channel = ctx.channel

        perms = channel.overwrites_for(ctx.guild.default_role)
        perms.send_messages = False

        try:
            await channel.set_permissions(ctx.guild.default_role, overwrite=perms, reason=f"[{ctx.author}]: channel lock ({channel.name})")            
        except Exception as err:
            return await ctx.channel.send(f"Don't expect me to know what happened >:)\n{err}")

        await ctx.channel.send("🔒 channel locked!")

    @_channel.command(name="unlock",usage="<channel>",description="These will revert changes from lock. Make sure that the role has send messages otherwise this wont change anything")
    @commands.has_permissions(manage_channels=True)
    async def _unlock(self, ctx, *,channel:discord.TextChannel=None):    

        if channel is None:
            channel = ctx.channel

        perms = channel.overwrites_for(ctx.guild.default_role)
        perms.send_messages = None

        try:
            await channel.set_permissions(ctx.guild.default_role, overwrite=perms, reason=f"[{ctx.author}]: channel unlock ({channel.name})")            
        except Exception as err:
            return await ctx.channel.send(f"Don't expect me to know what happened >:)\n{err}")

        await ctx.channel.send("🔓 channel unlocked!")

    @_channel.command(name="voicelock",usage="<channel>",description="Lock a channel so users can't speak in it.")
    @commands.has_permissions(manage_channels=True)
    async def _voicelock(self, ctx, *,channel:discord.VoiceChannel=None):    

        if channel is None:
            channel = ctx.channel

        perms = channel.overwrites_for(ctx.guild.default_role)
        perms.connect = False

        try:
            await channel.set_permissions(ctx.guild.default_role, overwrite=perms, reason=f"[{ctx.author}]: voice channel lock ({channel.name})")            
        except Exception as err:
            return await ctx.channel.send(f"Don't expect me to know what happened >:)\n{err}")

        await ctx.channel.send("🔈🔒 channel locked!")

    @_channel.command(name="voiceunlock",usage="<channel>",description="Allow users back into a previously locked voice channel.")
    @commands.has_permissions(manage_channels=True)
    async def _voiceunlock(self, ctx, *,channel:discord.VoiceChannel=None):    

        if channel is None:
            channel = ctx.channel

        perms = channel.overwrites_for(ctx.guild.default_role)
        perms.connect = None

        try:
            await channel.set_permissions(ctx.guild.default_role, overwrite=perms, reason=f"[{ctx.author}]: voice channel unlock ({channel.name})")            
        except Exception as err:
            return await ctx.channel.send(f"Don't expect me to know what happened >:)\n{err}")

        await ctx.channel.send("🔊🔓 channel unlocked!")
    
    @_channel.command(name="hide",usage="<channel>",description="Hide a channel from `@everyone`'s peeping eyes :eyes:")
    @commands.has_permissions(manage_channels=True)
    async def _hide(self, ctx, *,channel:discord.TextChannel=None):    

        if channel is None:
            channel = ctx.channel

        perms = channel.overwrites_for(ctx.guild.default_role)
        perms.view_channel = False

        try:
            await channel.set_permissions(ctx.guild.default_role, overwrite=perms, reason=f"[{ctx.author}]: channel hide ({channel.name})")            
        except Exception as err:
            return await ctx.channel.send(f"Don't expect me to know what happened >:)\n{err}")

        await ctx.channel.send("👀 channel now hidden! *If the user was viewing the channel while you ran the command they can still see it*")

    @_channel.command(name="unhide",usage="<channel>",description="Give `@everyone` permission to see the channel again like a good owner")
    @commands.has_permissions(manage_channels=True)
    async def _unhide(self, ctx, *,channel:discord.TextChannel=None):    

        if channel is None:
            channel = ctx.channel

        perms = channel.overwrites_for(ctx.guild.default_role)
        perms.view_channel = None

        try:
            await channel.set_permissions(ctx.guild.default_role, overwrite=perms, reason=f"[{ctx.author}]: channel hide ({channel.name})")            
        except Exception as err:
            return await ctx.channel.send(f"Don't expect me to know what happened >:)\n{err}")

        await ctx.channel.send("👀 channel now visible!")

    @_channel.command(name="voicehide",usage="<channel>",description="Hide a channel from `@everyone`'s peeping eyes :eyes: **(Voice Edition)**")
    @commands.has_permissions(manage_channels=True)
    async def _voicehide(self, ctx, *,channel:discord.VoiceChannel=None):    

        if channel is None:
            channel = ctx.channel

        perms = channel.overwrites_for(ctx.guild.default_role)
        perms.view_channel = False

        try:
            await channel.set_permissions(ctx.guild.default_role, overwrite=perms, reason=f"[{ctx.author}]: channel hide ({channel.name})")            
        except Exception as err:
            return await ctx.channel.send(f"Don't expect me to know what happened >:)\n{err}")

        await ctx.channel.send("👀 channel now hidden! *If the user was in the channel while it was being hidden they can stil see it.*")

    @_channel.command(name="voiceunhide",usage="<channel>",description="Give `@everyone` permission to see the channel again like a good owner **(Voice Edition)**")
    @commands.has_permissions(manage_channels=True)
    async def _voiceunhide(self, ctx, *,channel:discord.VoiceChannel):    

        if channel is None:
            channel = ctx.channel

        perms = channel.overwrites_for(ctx.guild.default_role)
        perms.view_channel = None

        try:
            await channel.set_permissions(ctx.guild.default_role, overwrite=perms, reason=f"[{ctx.author}]: channel hide ({channel.name})")            
        except Exception as err:
            return await ctx.channel.send(f"Don't expect me to know what happened >:)\n{err}")

        await ctx.channel.send("👀 channel now visible!")

    @commands.group(name="noroles",description="View my commands for more info you cutie <3")
    async def _noroles(self,ctx):
        return   

    @_noroles.command(name="show",description="Shows all users without a role in your server")
    @commands.has_permissions(manage_roles=True)
    async def _noroles_show(self,ctx):    
        
        list = []
        for x in ctx.guild.members:
            if x.roles == [ctx.guild.default_role]:
                list.append(x)
        length = [round(len(list) / 1)]
        pages = []

        Output = [list[x - y: x] for x, y in zip(accumulate(length), length)]         
        
        for x in Output:
            embed = discord.Embed(color=0x99AAB5,description='\n '.join(f'**{x.mention}**: `{x.id}`' for x in x))
            pages.append(embed)
        
        paginator = pagination.BotEmbedPaginator(ctx, pages)
        return await paginator.run()        

    @_noroles.command(name="prune",description="Removes all users from your server with no role.")
    @commands.has_permissions(manage_roles=True)
    async def _noroles_prune(self,ctx):    
        
        list = []
        for x in ctx.guild.members:
            if x.roles == [ctx.guild.default_role]:
                list.append(x)
        
        for x in list:
            try:
                await x.kick(reason=f"Auto kick: User has no roles.")
            except Exception as err:
                return await ctx.channel.send(f"Don't expect me to know what happened >:)\n{err}")

        await ctx.channel.send(f":ok_hand: {len(list)} users have been kicked!\n**Users kicked:**\n{', '.join(f'{x}' for x in list)}")

def setup(bot):
    bot.add_cog(admin(bot))
