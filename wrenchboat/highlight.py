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
    async def on_message(self,message):

        for x in self.bot.highlights:
            if self.bot.highlights[x]['phrase'] in message.content.lower() and self.bot.highlights[x]['guild'] == message.guild.id: 
                user = message.guild.get_member(self.bot.highlights[x]['author'])
                embed = discord.Embed(color=0x99AAB5,description=f"""{message.author}: {message.content.replace(self.bot.highlights[x]['phrase'], f"**{self.bot.highlights[x]['phrase']}**")}""")
                embed.set_author(name=self.bot.highlights[x]['phrase'].capitalize())
                embed.add_field(name="Jump through hyperspace to get the message!",value=f"[Click me to make the jump!]({message.jump_url})")
                await user.send(embed=embed)

def setup(bot):
    bot.add_cog(highlighter(bot))
