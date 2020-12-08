import collections
import os
import random
import sys

import aiohttp
import aioredis
import asyncpg
import discord 
from discord.ext import commands

import logging
import collections
import config
from logger import logging

class WrenchBoat(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=self.get_pre,
            case_insensitive=True,
            description="an easy to use bot for managing servers of any size.\n:warning: Errors are meant to be like that and im not being lazy :)",
            reconnect=True,
            status=discord.Status.idle,
            intents=discord.Intents(
                messages=True,
                guilds=True,
                members=True,
                guild_messages=True,
                dm_messages=True,
                reactions=True,
                guild_reactions=True,
                dm_reactions=True,
                voice_states=True,
                presences=True,
            ),
        )
        self.config = config
        self.session = None
        self.pool = None
        self.redis = None
        self.used = 0
        self.prefixes = {}
        self.automod = {}
        self.muteroles = {}
        self.modlog_channel = {}
        self.logging = {}
        self.highlights = {}
        self.cases = collections.defaultdict(lambda: 0)
        self.snips = {}

    async def get_pre(self, bot, message):

        return commands.when_mentioned_or(*config.prefix)(bot, message)

    async def start(self):
        self.session = aiohttp.ClientSession(loop=self.loop)

        await super().start(config.token)

    async def on_ready(self):
        self.pool = await asyncpg.create_pool(**self.config.db, max_size=150)
        self.redis = await aioredis.create_redis_pool(
            "redis://localhost", loop=self.loop
        )

        self.guild = self.get_guild(config.guild)
        self.modlogs = self.guild.get_channel(config.modlogs)

        for i in await self.pool.fetch("SELECT * FROM guilds"):
            """
            General Caching
            """

            self.prefixes[i["id"]] = i["prefix"]
            self.modlog_channel[i["id"]] = i["modlogs"]

            """
            Automod Caching
            """
            self.automod[i["id"]] = {"antihoist": i["antihoist"]}
            self.automod[i["id"]]["antinvite"] = (
                i["antinvite"]
                if i["antinvite"] in ["ban", "kick", "delete", "mute"]
                else None
            )
            self.automod[i["id"]]["antimassping"] = (
                i["antimassping"]
                if i["antimassping"] in ["ban", "kick", "delete", "mute"]
                else None
            )
            self.automod[i["id"]]["antiprofanity"] = (
                i["antiprofanity"]
                if i["antiprofanity"] in ["ban", "kick", "delete", "mute"]
                else None
            )
            self.automod[i["id"]]["antiraid"] = (
                {
                    "count": i["antiraid"].split(":")[0],
                    "action": i["antiraid"].split(":")[1],
                }
                if i["antiraid"]
                else None
            )
            self.automod[i['id']]['token_remover'] = i['token_remover']
            
            """
            Logging Caching
            """

            self.logging[i["id"]] = {"message_logs": i["messagelogs"],"server_logs": i["serverlogs"],"user_logs": i["userlogs"],"automod_logs": i["automodlogs"]}



        for i in await self.pool.fetch("SELECT * FROM infractions ORDER BY id DESC"):
            self.cases[i["guild"]] = i["id"]
        for i in await self.pool.fetch("SELECT * FROM highlights"):
            self.highlights[i["id"]] = {
                "phrase": i["phrase"],
                "author": i["author"],
                "guild": i["guild"],
            }

        try:
            with open("wrenchboat/utils/schema.sql") as f:
                await self.pool.execute(f.read())
        except Exception as e:
            print(f"Error in schema:\n{e}")

        await self.change_presence(
            status=discord.Status.online, activity=discord.Game("with wrenches")
        )
        logging.info("Bot started loading modules")
        
        for ext in config.extensions:
            try:
                self.load_extension(f"{ext}")
            except Exception as e:
                print(f"Failed to load {ext}, {e}")
                logging.fail(ext)

        logging.info(f"Bot started. Guilds: {len(self.guilds)} Users: {len(self.users)}")

    async def on_message(self, message):

        if message.author.bot:
            return
        
        if not message.guild:
            return

        ctx = await self.get_context(message)

        if ctx.command:
            await self.process_commands(message, ctx)

    async def process_commands(self, message, ctx):

        if ctx.command is None:
            return

        self.used += 1
        await self.invoke(ctx)

    async def on_guild_join(self, guild):

        if guild.id not in config.guild_whitelist:
            await guild.leave()

        try:
            i = await self.pool.fetchrow(
                "INSERT INTO guilds(id,prefix) VALUES($1,$2) RETURNING *",
                guild.id,
                "!w",
            )
            self.automod[i["id"]] = {
                "antihoist": i["antihoist"],
                "antinvite": i["antinvite"],
            }
        except KeyError:
            pass


if __name__ == "__main__":
    WrenchBoat().run()
