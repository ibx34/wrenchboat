from textwrap import dedent
import config
import discord
from discord.ext import commands


class HelpCommand(commands.MinimalHelpCommand):
    def __init__(self):
        super().__init__(command_attrs={"hidden": True})

    def get_command_signature(self, command):
        return "{0.clean_prefix}{1.qualified_name} {1.signature}".format(self, command)

    async def send_bot_help(self, mapping):

        ctx = self.context
        prefix = ctx.prefix  # config.prefix

        str = "\n".join(x for x in ctx.bot.cogs if x not in ["Jishaku", "Help", "AutoModeration", "Error", "highlighter", "listeners", "_purge"])
        await ctx.send(
            f"{ctx.bot.description}\n\n**Categories**:\n{str}\n\nType `{prefix}help command` for more info on a command.\nYou can also type `{prefix}help category` for more info on a category.\n*Ps: the really good avatar was made by some nerd A5rocks#9289 ~~also a simp~~*"
        )

    async def send_cog_help(self, cog):

        ctx = self.context
        prefix = ctx.prefix

        commands = cog.get_commands()
        str = "\n".join(f"**{x.name}** {x.description}" for x in commands)

        await ctx.send(
            f"{str}\n\nType `{prefix}help command` for more info on a command.\nYou can also type `{prefix}help category` for more info on a category."
        )

    async def send_command_help(self, command):

        ctx = self.context
        prefix = ctx.prefix

        await ctx.send(
            f"{command.description}\n\n`{prefix}{command} {command.usage}`\n\nType `{prefix}help command` for more info on a command.\nYou can also type `{prefix}help category` for more info on a category."
        )

    async def send_group_help(self, group):

        ctx = self.context
        prefix = ctx.prefix
        command = ctx.bot.get_command(group.name)

        str = "\n".join(f"**{x.name}** {x.description}" for x in group.commands)
        await ctx.send(
            f"{command.description}\n\n`{prefix}{command} {command.usage}`\n\n**Commands**:\n{str}\n\nType `{prefix}help command` for more info on a command.\nYou can also type `{prefix}help category` for more info on a category."
        )


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.old_help_command = bot.help_command
        bot.help_command = HelpCommand()
        bot.help_command.cog = self


def cog_unload(self):
    self.bot.help_command = self.old_help_command


def setup(bot):
    bot.add_cog(Help(bot))
