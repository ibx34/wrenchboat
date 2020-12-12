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