from textwrap import dedent

import config
import discord
from discord.ext import commands


class logging(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message_delete(self,message):
        if message.author.bot:
            return
        
        self.bot.snips[message.channel.id] = {"author": message.author,"content": message.content, "message_created":message.created_at, "channel": message.channel}

        if not self.bot.logging.get(message.guild.id).get("message_logs"):
            return

        logs = self.bot.get_channel(self.bot.logging[message.guild.id]['message_logs'])
        embed = discord.Embed(description=f"**{message.author}** ({message.author.id}) deleted message:")
        embed.add_field(name="Content",value=message.content or "No message content")
        embed.set_image(url=message.attachments[0].proxy_url) if message.attachments else None

        await logs.send(embed=embed)
    
    @commands.Cog.listener()
    async def on_message_edit(self,before,after):    
        if before.author.bot:
            return
        
        if not self.bot.logging.get(after.guild.id).get("message_logs"):
            return

        if before.content.lower() == after.content.lower():
            return
            
        logs = self.bot.get_channel(self.bot.logging[after.guild.id]['message_logs'])

        if after.pinned:
            embed = discord.Embed(description=f"**{after.channel.mention}** new pinned [message]({after.jump_url}):")
            embed.add_field(name="Content",value=after.content,inline=False)     
            return await logs.send(embed=embed)       

        embed = discord.Embed(description=f"**{after.author}** ({after.author.id}) updated [message]({after.jump_url}):")
        embed.add_field(name="New Content",value=after.content,inline=False)
        embed.add_field(name="Old Content",value=before.content,inline=False)

        await logs.send(embed=embed)

def setup(bot):
    bot.add_cog(logging(bot))
