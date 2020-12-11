import discord
from discord.ext import commands

in_line_responses = {
    "normal": {"en": "[{guild}] {user} has been {action}."},
    "compact": {"en": "{user} has been {action}."},
    "advanced": {
        "en": "**{guild}** | {moderator} {action} {user} for {time} ({reason})."
    },
    "simple": {"en": "Done."},
    "even_simpler": ":ok_hand:",
}


class Responder:
    def __init__(self, bot):
        self.bot = bot

    @classmethod
    async def in_line(cls, ctx, user, action: str, reason, time="Indefinite"):
        # En is currently the only language >:)
        returned_message = in_line_responses[ctx.bot.guild_responses[ctx.guild.id]]["en"]
        await ctx.channel.send(returned_message.format(
                guild=ctx.guild,
                moderator=ctx.author,
                action=action + "ed",
                reason=reason,
                time=time,
                user=user,
            )
        )

