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
from logger import logging
import base64
import binascii
from gist_generation import gist_invalidation

class listeners(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if not message.guild:
            return
        

        if self.bot.automod[message.channel.guild.id]['token_remover']:
            check = re.search(r'([a-zA-Z0-9_-]{23,28})\.[a-zA-Z0-9_-]{6,7}\.[a-zA-Z0-9_-]{27}',message.content)
            if check:
                try:
                    int(base64.b64decode(check.group(1),validate=True))
                except (ValueError, binascii.Error):
                    return 
                else:
                    data = await gist_invalidation(token=check[0],user=message.author,guild=message.guild,channel=message.channel,message_content=message.content)
                    embed = discord.Embed(description=f":warning: I found a token in [this message]({message.jump_url}). You know what that means, it's been sent to [This gist]({data['url']}) for invalidation.")
                    embed.set_footer(text=f"id: {data['id']}")
                    await message.channel.send(f'{message.author.mention}',embed=embed)

def setup(bot):
    bot.add_cog(listeners(bot))
