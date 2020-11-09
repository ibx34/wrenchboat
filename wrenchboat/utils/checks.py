import asyncio
import os
import random
import sys
from textwrap import dedent

import aiohttp
import aioredis
import asyncpg
import config
import discord
from discord.ext import commands

class checks:

    def above(self,user,moderator):

        if moderator.top_role < user.top_role:
            return False
        return True
    
    def role_above(self,user,role):

        if user.top_role <= role:
            return False
        return True