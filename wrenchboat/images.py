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

    @commands.command(name="pat")
    async def _pat(self,ctx,user:discord.Member):
        
        url=random.choice(pat)
        embed = discord.Embed(color=0x99AAB5,description=f"**{ctx.author.display_name}** pats **{user.display_name}**")
        embed.set_image(url=url)
        await ctx.channel.send(embed=embed)

def setup(bot):
    bot.add_cog(images(bot))
