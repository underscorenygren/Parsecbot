from discord.ext import commands
from discord import Color, Embed
import asyncio
import requests
from time import time
import json
from os import path
from datetime import datetime


class eSupport:

    def __init__(self, bot):
        self.bot = bot
        self.time = 0
        self.run = asyncio.Event(loop=bot.loop)
        self.elist = []
        self.emodify = {}
        self.task = self.bot.loop.create_task(self.scrapeTask())

        self.run.set()

        if path.exists('errors.private') and path.isfile('errors.private'):
            with open('errors.private', 'r') as file:
                self.emodify = json.load(file)
                print('Loaded error data')
        else:
            with open('errors.private', 'w') as file:
                json.dump(self.emodify, file)

    def save(self):
        with open('errors.private', 'w') as file:
            json.dump(self.emodify, file)

    async def scrapeTask(self):
        url = "https://support.parsecgaming.com/hc/en-us/sections/115000849851"
        while True:
            await self.run.wait()  # Wait until triggered

            if self.time > time() - 60:
                self.run.clear()
                print("Skipping requested scrape")
                return  # Don't repeat more than once a minute

            print("Performing requested scrape")
            r = requests.get(url)

            data = []
            for item in r.iter_lines():
                if "Error Codes - " in str(item):
                    data.append(str(item))

            errorlist = []
            for i in data:
                tl = {}

                v = "https://support.parsecgaming.com" + i.split("\"")[1][:31]
                tl['url'] = v

                tmp = i.split(">")[1].split("<")[0].replace("&#39;", "'")

                v = [w for w in tmp.split("(")[0].split() if w.isdigit()]
                tl['code'] = v

                tl['title'] = tmp
                tl['desc'] = tmp[len(tmp.split("(")[0])+1:-1]

                errorlist.append(tl)
            self.elist = errorlist

            self.time = time()
            self.run.clear()

    async def checkNums(self, message):
        tmp = message.content.split()
        for i in tmp:
            if i.isdigit() or i in self.emodify.keys():
                # If any 'word' in the message is a number, or a manual error.
                self.run.set()
                return await self.errorProcess(message, i, False)

    async def checkWords(self, message):
        for code in self.emodify.keys():
            if code.lower() in message.content.lower():
                self.run.set()
                return await self.errorProcess(message, code, False)

    def is_admin():
        async def predicate(ctx):
            # Is the command user Kodikuu?
            c1 = ctx.author.id == 124207277174423552
            # Is the command user the current bot owner?
            c2 = ctx.author.id == ctx.bot.owner_id
            # Does the command user have the Jedi role?
            c3 = ctx.author.top_role.name == "Jedi"
            # Does the command user have the Parsec Team role?
            c4 = ctx.author.top_role.name == "Parsec Team"
            return c1 or c2 or c3 or c4
        return commands.check(predicate)

    @commands.command()
    @is_admin()
    async def scrape(self, ctx):
        self.time = 0
        self.run.set()

    @commands.command()
    async def error(self, ctx, errorcode):
        # Just makes things easier when running errorprocess not as a command.
        self.run.set()
        await self.errorProcess(ctx, errorcode, True)

    @commands.command()
    @is_admin()
    async def erroredit(self, ctx, code, key, *desc):

        if key not in ["title", "url", "desc", "remove"]:
            ctx.send("Invalid key to edit")

        if code not in self.emodify.keys():
            self.emodify[code] = {}

        if key == "remove":
            del self.emodify[code]
        else:
            self.emodify[code][key] = ' '.join(desc)
        self.save()
        await ctx.message.add_reaction("🆗")
        await asyncio.sleep(5)
        await ctx.message.clear_reactions()

    async def errorProcess(self, ctx, ecode, explicit=False):
        # Get scraped error
        error = None
        for e in self.elist:
            if error is not None:
                break
            for code in e['code']:
                if ecode == code:
                    error = e
                    # Correct error with persistent modifications.
                    if ecode in self.emodify.keys():
                        for key in self.emodify[ecode].keys():
                            error[key] = self.emodify[ecode][key]
                    break
        else:
            # Search through persistence data for manually added key
            if ecode in self.emodify.keys():
                error = self.emodify[ecode]

            else:
                if explicit:
                    desc = "Please contact staff or correct your error code."
                    emb = Embed(title=f"{ecode}: Not Documented.",
                                description=desc,
                                timestamp=datetime.now(),
                                color=Color.dark_red())
                    await ctx.channel.send(embed=emb)
                return  # No error found

        # Ensure error is complete, input placeholders if not
        for key in ["title", "desc", "url"]:
            if key not in error.keys():
                error[key] = ""

        await self.errorResponse(ctx, error, explicit)
        return True

    async def errorResponse(self, ctx, error, explicit=False):
        def check(reaction, user):
            e = str(reaction.emoji)
            return e == '❎' or e == '✅' and not user == self.bot.user

        # Output error immediately if explicit.
        if explicit:
            rembed = Embed(title=error['title'],
                           description=error['desc'],
                           url=error['url'],
                           timestamp=datetime.now(),
                           color=Color.dark_red())
            await ctx.channel.send(embed=rembed)

        else:  # Go through steps if not explicit
            await ctx.add_reaction("❎")
            await ctx.add_reaction("✅")
            try:
                reaction, user = await self.bot.wait_for('reaction_add',
                                                         timeout=60.0,
                                                         check=check)
            except asyncio.TimeoutError:
                await ctx.clear_reactions()
            else:
                await ctx.clear_reactions()
                if str(reaction.emoji) == '✅':
                    await ctx.add_reaction("🆗")
                    rembed = Embed(title=error['title'],
                                   description=error['desc'],
                                   url=error['url'],
                                   timestamp=datetime.now(),
                                   color=Color.dark_red())
                    await ctx.channel.send(embed=rembed)
                    await asyncio.sleep(5)
                    await ctx.clear_reactions()
