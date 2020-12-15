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
from discord.ext import commands

from wrenchboat.utils import pagination


class highlighter(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):

        for x in self.bot.highlights:
            if (
                self.bot.highlights[x]["phrase"] in message.content.lower()
                and self.bot.highlights[x]["guild"] == message.guild.id
            ):
                user = message.guild.get_member(self.bot.highlights[x]["author"])
                embed = discord.Embed(
                    color=0x99AAB5,
                    description=f"""{message.author}: {message.content.replace(self.bot.highlights[x]['phrase'], f"**{self.bot.highlights[x]['phrase']}**")}""",
                )
                embed.set_author(name=self.bot.highlights[x]["phrase"].capitalize())
                embed.add_field(
                    name="Jump through hyperspace to get the message!",
                    value=f"[Click me to make the jump!]({message.jump_url})",
                )
                await user.send(embed=embed)


def setup(bot):
    bot.add_cog(highlighter(bot))
