# Core Requirements.
from discord.ext import commands
from discord import Activity, ActivityType, AppInfo, Embed, utils
import asyncio
import subprocess
from random import choice

# Uncomment this with a full IDE, it should warn that it's not in use
# The idea being that we never import EVERYTHING. We don't need it all
# import discord

# File IO (Cryptographically Insecure)
import json
from os import path

# Additional Requirements
import checks
import errorSupport
import DynamicVoice


# Pre-start configuration and token loading
if path.exists('core.private') and path.isfile('core.private'):
    with open('core.private', 'r') as file:
        core = json.load(file)

    if 'token' not in core.keys():
        print('Token Missing.')
        core['token'] = input('Token: ')
        with open('core.private', 'w') as file:
            json.dump(core, file)
else:
    print('Core data is missing.')

    token = input('Token: ')
    if token == '':
        raise ValueError('Invalid Token: Empty String')

    core = {'token': token,
            }
    del token  # We don't want extra auth token copies lying around.

    with open('core.private', 'x') as file:
        json.dump(core, file)

# Pre-start setup
bot = commands.AutoShardedBot(command_prefix=commands.when_mentioned_or('>'))
bot.activity = Activity(type=ActivityType.watching,
                        name='Parsec develop.')
state = {'state': 'starting',
         'persistent': {},
         'client': bot,
         'ready_event': asyncio.Event(loop=bot.loop),
         'etime': 0,
         'erun': asyncio.Event(loop=bot.loop),
         }

if path.exists('persistence.private') and path.isfile('persistence.private'):
    with open('persistence.private', 'r') as file:
        state['persistent'] = json.load(file)
        print('Loaded persistent data')
else:
    with open('persistence.private', 'x') as file:
        json.dump(state['persistent'], file)


# Background Tasks

# Function + Event Definitions
@bot.event
async def on_message(message):
    # Return if bot message
    if message.author == bot.user:
        return

    # Anything that isn't a command goes inside this 'if' statement.
    if not (message.content.startswith(">") or bot.user in message.mentions):
        # Look for error codes if a command isn't used.
        if await eSupport.checkMessage(message):
            return

        # Good Bot. Bad Bot.
        if "good bot" in message.content.lower():
            await message.channel.send("I do my best 😄")
        elif "bad bot" in message.content.lower():
            await message.channel.send("I blame Kodikuu. All his fault.")

        # Implement basic anti-spam

    await bot.process_commands(message)


@bot.event
async def on_command_error(ctx, error):
    m_bot = any([user.bot for user in ctx.message.mentions])

    if isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have permission to use that command.")

    elif isinstance(error, commands.errors.CommandNotFound) and not m_bot:
        await ctx.send(error)

    elif not m_bot:
        await ctx.send(error)
        raise error


async def saveP():
    with open('persistence.private', 'w') as file:
        json.dump(state['persistent'], file)


# Commands
@bot.command()
async def tldr(ctx):
    embed = Embed(title="TL;DR: What is Parsec?", color=0x5c5cff)
    embed.description = (
        "Think of Parsec like a fast screen-sharing software where your "
        "friend's controller acts as if it were plugged into your PC "
        "locally. In other words, it's as if your friend was "
        "**right next to you** looking at your screen and with his own "
        "controller."
        "\n\n"
        "This will work any game, emulator or program where your "
        "friend's controller is used, like split-screen games."
        "\n\n"
        "This doesn't work like Hamachi, where you're supposed to have 2 "
        "different games/PCs, one connecting to the other via LAN or "
        "something.")

    text = (
        "Parsec is intended to make it easier for you to play the games "
        "you love, whether with friends or alone.")

    await ctx.send(text, embed=embed)


@bot.command()
@checks.moderator()
async def hero(ctx, user):
    if user.isdigit():
        member = utils.find(lambda m: str(m.id) == user, ctx.guild.members)
    elif len(ctx.message.mentions):
        member = ctx.message.mentions[0]

    if member is None:
        await ctx.send(f"Could not find user {user}")
        return False

    hero = utils.find(lambda m: m.name.lower() == "hero", ctx.guild.roles)
    name = member.nick or member.name

    if hero in member.roles:
        await member.remove_roles(hero)
        response = choice([f"{name} has turned to a life of villainy!",
                           f"{name} decided to retire from a life of heroism.",
                           f"{name} lived long enough to see themselves become the villain...",
                           f"Some kyptonite fell on {name}, they lost their powers!"])
        await ctx.send(response)

    else:
        await member.add_roles(hero)
        response = choice([f"{name} got hit by gamma radiation and turned green!",
                           f"{name} stood up the challenge, and came out victorious!",
                           f"What kind of person is {name}? A Hero!",
                           f"{name} is cooler than a cucumber, and greener still."])
        await ctx.send(response)
        return


@bot.command()
@checks.moderator()
async def gamedev(ctx, user):
    if user.isdigit():
        member = utils.find(lambda m: str(m.id) == user, ctx.guild.members)
    elif len(ctx.message.mentions):
        member = ctx.message.mentions[0]

    if member is None:
        await ctx.send(f"Could not find user {user}")
        return False

    gdev = utils.find(lambda m: m.name.lower() == "game devs", ctx.guild.roles)
    name = member.nick or member.name

    if gdev in member.roles:
        await member.remove_roles(gdev)
        response = choice([f"{name} decided game development was hard.", ])
        await ctx.send(response)

    else:
        await member.add_roles(gdev)
        response = choice([f"{name} got hit by gamma radiation and turned... blue?!",
                           f"{name} stood up the challenge, and built something awesome!",
                           f"What kind of person is {name}? A Developer!",
                           f"{name} is cooler than a cucumber, and... well, far bluer."])
        await ctx.send(response)


@bot.command()
@checks.admin()
async def update(ctx):
    await ctx.send('Attempting to update.')
    code = subprocess.call(["git", "pull"])
    if code == 0:
        await ctx.send(f"Finished update with exit code {code}. Restarting.")
        exit()
    else:
        await ctx(f"Update resulted in code {code}. Not restarting.")


@bot.command(description='Restart the bot.')
@checks.trusted()
async def restart(ctx):
    await ctx.send('Restarting.')
    exit()


@bot.command(description='Shut down the bot.', hidden=True)
@checks.admin()
async def quit(ctx):
    await ctx.send('Shutting Down.')
    state['state'] = 'shutdown'
    await bot.logout()


@quit.error
async def quit_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send(f'Only {AppInfo.owner} may shut me down.')
    elif ctx.author.id == bot.owner_id:
        await ctx.send('Something went very *very **wrong.***')

# Initialise module classes
eSupport = errorSupport.eSupport(bot)
bot.add_cog(eSupport)

dVoice = DynamicVoice.DynamicVoice(bot)
bot.add_cog(dVoice)

# Register tasks

# Start bot
print('Starting Bot')

bot.run(core['token'])

if state['state'] == 'shutdown':
    exit(0x78)
else:
    exit()
