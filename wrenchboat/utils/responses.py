import discord
from discord.ext import commands

responses = {
    "in_channel_responses": {
        "normal": {"en": "[{guild}] {user} has been {action}."},
        "compact": {"en": "{user} has been {action}."},
        "advanced": {
            "en": "**{guild}** | {moderator} {action} {user} for {time} ({reason})."
        },
        "simple": {"en": "Done."},
        "even_simpler": ":ok_hand:",
    }
}


class Responder:
    def __init__(self, bot):
        self.bot = bot

    async def in_line(
        self, ctx, user, guild, action: str, reason, respone, time="Indefinite"
    ):
        # En is currently the only language >:)
        response = responses["in_channel_responses"][
            self.bot.guild_responses(guild.id)
        ]["en"]
        await ctx.send(
            response.format(
                guild=guild,
                moderator=ctx.author,
                action=action + "ed",
                reason=reason,
                time=time,
                user=user,
            )
        )

