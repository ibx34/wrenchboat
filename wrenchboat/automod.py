import os
import random
import re
import sys

import aiohttp
import aioredis
import asyncpg
import config
import discord
from discord.ext import commands

from wrenchboat.assets.words import list


class Switch(object):
    def __init__(self, user, message, bot, word):
        self.message = message
        self.user = user
        self.bot = bot
        self.word = word

    def Actions(self, action):
        method = getattr(self, action, lambda: "Invalid Action")
        return method()

    async def delete(self):
        return await self.message.delete()

    async def ban(self):
        return await self.user.ban(
            reason=f"[AutoModeration]: {self.message.author} ({self.message.author.id}) mentioned a blacklisted word."
        )

    async def kick(self):
        return await self.user.kick(
            reason=f"[AutoModeration]: {self.message.author} ({self.message.author.id}) mentioned a blacklisted word."
        )

    async def mute(self):
        async with self.bot.pool.acquire() as conn:
            guild = await conn.fetchrow(
                "SELECT * FROM guilds WHERE id = $1", self.user.guild.id
            )

            try:
                muted = self.user.guild.get_role(guild["muterole"])
                dontmuterole = self.user.guild.get_role(guild["dontmute"])

                if dontmuterole in self.user.roles:
                    return

                return await self.user.add_roles(
                    muted, reason=f'Automod mute: word mentioned: "{self.word}"'
                )
            except:
                return


class AutoModeration(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if self.bot.automod.get(message.guild.id) is None:
            return

        for x in list:
            if x in message.content:

                await Switch(
                    user=message.author, message=message, bot=self.bot, word=x
                ).Actions(action=self.bot.automod.get(message.guild.id))

    @commands.Cog.listener()
    async def on_member_update(self, before, after):
        if before.bot:
            return

        user = before.guild.get_member(before.id)
        if user.nick:
            if self.bot.antihoist.get(before.guild.id) is False:
                return
                
            for x in config.characters:
                if after.nick.startswith(x):
                    await user.edit(
                        nick=random.choice(config.clean_names), reason="Name sanitation"
                    )


def setup(bot):
    bot.add_cog(AutoModeration(bot))
