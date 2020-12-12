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
import discord
from discord.ext import commands

import config
from wrenchboat.assets.images import pat
from wrenchboat.utils import pagination
from wrenchboat.utils.checks import checks
from wrenchboat.utils.modlogs import modlogs


class images(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="pat", usage="@user", description="Show your love by giving some cutie a pat. ~Baka")
    async def _pat(self,ctx,user:discord.Member=None):

        if user is None:
            return await ctx.send(f"Provide a person to {ctx.command.name} silly")

        async with aiohttp.ClientSession() as cs:
            async with cs.get("https://api.tenor.com/v1/random?q=anime pat&key=9SY3T59FQIOA&limit=1&media_filter=minimal&contentfilter=high") as r:
                data = await r.json()
                hmm = list(data['results'])
                await ctx.channel.send(f"**{ctx.author.display_name}** pats **{user.display_name}**\n{hmm[0]['url']}")

    @commands.command(name="hug", usage="@user", description="hug someone who just needs a hug ~<3")
    async def _hug(self,ctx,user:discord.Member=None):

        if user is None:
            return await ctx.send(f"Provide a person to {ctx.command.name} silly")

        async with aiohttp.ClientSession() as cs:
            async with cs.get("https://api.tenor.com/v1/random?q=anime hug&key=9SY3T59FQIOA&limit=1&media_filter=minimal&contentfilter=high") as r:
                data = await r.json()
                hmm = list(data['results'])
                await ctx.channel.send(f"**{ctx.author.display_name}** hugs **{user.display_name}**\n{hmm[0]['url']}")

    @commands.command(name="poke", usage="@user", description="If someone annoys you... just poke them OwO")
    async def _poke(self,ctx,user:discord.Member=None):

        if user is None:
            return await ctx.send(f"Provide a person to {ctx.command.name} silly")

        async with aiohttp.ClientSession() as cs:
            async with cs.get("https://api.tenor.com/v1/random?q=anime poke&key=9SY3T59FQIOA&limit=1&media_filter=minimal&contentfilter=high") as r:
                data = await r.json()
                hmm = list(data['results'])
                await ctx.channel.send(f"**{ctx.author.display_name}** pokes **{user.display_name}**\n{hmm[0]['url']}")

    @commands.command(name="slap", usage="@user", description="Someone being rude, then put them in their place by slapping them!")
    async def _slap(self,ctx,user:discord.Member=None):

        if user is None:
            return await ctx.send(f"Provide a person to {ctx.command.name} silly")

        async with aiohttp.ClientSession() as cs:
            async with cs.get("https://api.tenor.com/v1/random?q=anime slap&key=9SY3T59FQIOA&limit=1&media_filter=minimal&contentfilter=high") as r:
                data = await r.json()
                hmm = list(data['results'])
                await ctx.channel.send(f"**{ctx.author.display_name}** slap **{user.display_name}**\n{hmm[0]['url']}")

    @commands.command(name="kiss", usage="@user", description="Kiss your special someone ~! Cuties")
    async def _kiss(self,ctx,user:discord.Member=None):

        if user is None:
            return await ctx.send(f"Provide a person to {ctx.command.name} silly")

        async with aiohttp.ClientSession() as cs:
            async with cs.get("https://api.tenor.com/v1/random?q=anime kiss&key=9SY3T59FQIOA&limit=1&media_filter=minimal&contentfilter=medium") as r:
                data = await r.json()
                hmm = list(data['results'])
                await ctx.channel.send(f"**{ctx.author.display_name}** kisses **{user.display_name}**\n{hmm[0]['url']}")

    @commands.command(name="punch", usage="@user", description="No description needed for this one...")
    async def _punch(self,ctx,user:discord.Member=None):

        if user is None:
            return await ctx.send(f"Provide a person to {ctx.command.name} silly")

        async with aiohttp.ClientSession() as cs:
            async with cs.get("https://api.tenor.com/v1/random?q=anime punch&key=9SY3T59FQIOA&limit=1&media_filter=minimal&contentfilter=medium") as r:
                data = await r.json()
                hmm = list(data['results'])
                await ctx.channel.send(f"**{ctx.author.display_name}** punches **{user.display_name}**\n{hmm[0]['url']}")

def setup(bot):
    bot.add_cog(images(bot))
