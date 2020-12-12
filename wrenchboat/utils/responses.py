import discord
from discord.ext import commands
from logger import logging

in_line_responses = {
    "normal": {
        "en": "[{guild}] {user} has been {action}.",
        "es": "[{guild}] {user} tiene estado {action}.",
        "la": "[{guild}] {user} habet fuit {action}."
    },
    "compact": {
        "en": "{user} has been {action}.",
        "es": "{user} tiene estado {action}.",
        "la": "{user} habet fuit {action}."
    },
    "advanced": {
        "en": "**{guild}** | {moderator} {action} {user} for {time} ({reason}).",
        "es": "**{guild}** | {moderator} {action} {user} para {time} ({reason}).",
        "la": "**{guild}** | {moderator} {action} {user} quia {time} ({reason})."
    },
    "simple": {
        "en": "Done.",
        "es": "Hecho.",
        "la": "Factum.",
    },
    "even_simpler": ":ok_hand:",
}


class Responder:
    def __init__(self, bot):
        self.bot = bot

    @classmethod
    async def in_line(cls, ctx, user, action: str, reason, time="Indefinite"):
        # En is currently the only language >:)
        returned_message = in_line_responses[ctx.bot.guild_responses[ctx.guild.id]][ctx.bot.language[ctx.channel.guild.id]]
        try:
            await ctx.channel.send(returned_message.format(
                    guild=ctx.guild,
                    moderator=ctx.author,
                    action=action + "ed",
                    reason=reason,
                    time=time,
                    user=user,
                )
            )
        except Exception as err:
            logging.fail(err)
