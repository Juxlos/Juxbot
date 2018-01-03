#
#       Rewrite
#       JuxBot
#       By Juxlos
#       Version: 0.0.0.7
#       January 3, 2018

#   Import libraries
import asyncio
import math
import random
import json
import time
import sys
import datetime
try:
    from discord.ext import commands
    import discord
except ImportError:
    print("Discord.py is not installed.\n"
          "Consult the guide for your operating system "
          "and do ALL the steps in order.\n")
    sys.exit(1.5)

           
#   API Key, Admin ID, etc.
import config
    
#   Setup connection to client, and setup a bot instance
bot = discord.Client()

#   Load vars here
#   Load big vars here
number_of_q = 2 # Number of questions in the personality test


#   Loads pmd.json - raw data for the entire PMD section of the bot
with open('pmd.json') as pfile:
    pmd_json = json.load(pfile)
with open('data.json') as dfile:
    data = json.load(dfile)
with open('users.json') as ufile:
    user_data = json.load(ufile)
with open('level_stats.json') as lstfile:
    level_stats = json.load(lstfile)
#       Insert other defs here


#   jsonwrite() writes var data to data.json
#   user_write() writes user_data to users.json
#   Don't hate me
def jsonwrite():
    with open('data.json', 'w') as target:
        json.dump(data, target, indent=4, separators=(',', ': '))


def userwrite():
    with open('users.json', 'w') as userbase:
        json.dump(user_data, userbase, indent=4, separators=(',',':' ))


def date_time(t=time.time()):
    st = datetime.datetime.fromtimestamp(t).strftime('%Y-%m-%d %H:%M:%S')
    return st + " UTC"


#   Whitelist of servers
async def authorize_server(message):
    if message.server.id not in data['servers']:
        data['servers'][message.server.id] = {'active_commands': [], 'authorized_at': time.time()}
        await bot.send_message(message.channel, 'Server authorized!')
        jsonwrite()
    else:
        await bot.send_message(message.author, 'Already done a while back you fuck.')


#   Basic general functions
def IsInt(s):
    try:
        int(s)
        return True
    except ValueError:
        return False


#   Help message
async def help_message(target):
    command_list = data['command_list']
    names = list(command_list.keys())
    #   Names are by default all commands
    #   This cuts admin commands
    if target.id not in config.admin_id:
        names = [name for name in names if command_list[name]["admin_only"] is False]
    text = ['```']
    for name in names:
        try:
            text.append(name+' | '+command_list[name]['summary'])
        except KeyError:
            # No summary case
            text.append(name)
    text.append('```')
    await bot.send_message(target, '\n'.join(text))


#   Checks cooldown for a command
#   e.g. check_cooldown(';pmdquiz')
#   Automatically checks wait period
async def check_cooldown(command, message):
    # Admin bypass
    if message.author.id in config.admin_id:
        return[True, 0]
    k = time.time()
    if command in list(data['command_list'].keys()):
        cd = data['command_list'][command]
        if "cooldown" in list(cd.keys()):
            if "last_use" in list(cd.keys()):
                # Normal case
                if k - cd['last_use'] > cd['cooldown']:
                    cd['last_use'] = k
                    data['command_list'][command] = cd
                    jsonwrite()
                    return [True]
                # Rejected
                else:
                    v = int(cd['cooldown']+cd['last_use']-k)
                    cd_text = "Please wait {0} seconds.".format(v)
                    await bot.send_message(message.channel, cd_text)
                    return[False, cd_text]
            # First use
            else:
                cd['last_use'] = k
                data['command_list'][command] = cd
                jsonwrite()
                return [True, 0]
        # No cooldown just in case
        else:
            return [True, 0]
    else:
        print("Error: Requested cooldown for non-existent command")
        return[False, 0]

#   Better than writing it each time
def toggle_command(command, server_id, on_or_off="on"):
    if command in list(data['command_list'].keys()):
        if server_id in list(data['servers'].keys()):
            if 'active_commands' in list(data['servers'][server_id].keys()):
                ac = data['servers']['server']['active_commands']
                if on_or_off is "on":
                    if command in ac:
                        pass
                    else:
                        data['servers']['server']['active_commands'].append(command)
                else:
                    if command in ac:
                        data['servers']['server']['active_commands'] = [x for x in ac if x != command]
            elif on_or_off == "on":
                data['servers']['server']['active_commands'] = [command]
        else:
            #   Presumed authorized
            authorize_server(server_id)
            if on_or_off == "on":
                data['servers']['server']['active_commands'].append(command)
        jsonwrite()
    else:
        print('Error: Requested activation of nonexistent command!')


#   See above
def active_commands(command, server):
    if command in list(data['command_list'].keys()):
        if server.id in list(data['servers'].keys()):
            active_command_list = data['servers'][server.id]['active_commands']
        else:
            # Unauthorized server or DMs - must be in authorized ones
            return False
        # Only listed as False anyway
        if "sim" in list(data['command_list'][command].keys()):
            if command in active_command_list:
                return False
            else:
                return True
        # For "fine-to-be-simultaneous-commands"
        else:
            return True


#   PMD-related commands
class PMDModule:
    def __init__(self):
        self.bot = bot

    def getPMDquestions(self, n):
        #   Gets the list of questions available
        q = list(pmd_json['questions'].keys())
        if len(q) < n:
            n = len(q)
        l = []
        while len(l) < n:
            l.append(random.choice([x for x in q if x not in l]))
        return l

    def traitadd(self, t, var, n):
        if t in list(var.keys()):
            var[t] += n
        else:
            var[t] = n
        return var

    #   Gets Pokedex Number from a Pokemon name
    def get_dex_no(self, poke):
        dex_no = [t for t in list(pmd_json['poke'].keys()) if pmd_json['poke'][t] == poke][0]
        return dex_no

    def generate_bst(self, poke, level):
        dex_no = self.get_dex_no(poke)
        nos = list(level_stats.keys())
        match = []
        for n in nos:
            if poke == level_stats[n]["name"]:
                match.append(level_stats[n])
        bst = match[0]
        #   Gives stats for just 1 level instead of all of them
        specstats = bst['stats'][str(level)]
        bst['dex_no'] = dex_no
        bst['stats'] = specstats
        bst['level'] = int(level)
        return bst

    async def personality_test(self, message):
        check = True
        if message.author.id in list(user_data.keys()):
            check = False
            kp = await self.bot.send_message(message.author, 'You have taken this personality test before.')
            await asyncio.sleep(1)
            await self.bot.send_message(message.author, 'Taking this again will reset your entire progress.\n'+\
                                                        'Would you like to continue? Say "YES" if you do.')
            confirm = await self.bot.wait_for_message(timeout = 10, channel = kp.channel, author = message.author)
            if confirm is not None:
                if confirm.content.lower() in ["yes"]:
                    await self.bot.send_message(message.author, '...')
                    await asyncio.sleep(3.5)
                    await self.bot.send_message(message.author, '...Are you sure?')
                    confirm = await self.bot.wait_for_message(timeout=15, channel=kp.channel, author=message.author)
                    if confirm is not None:
                        if confirm.content.lower() in ["yes", "y"]:
                            await self.bot.send_message(message.author, '...')
                            await asyncio.sleep(2)
                            await self.bot.send_message(message.author, '...Alright. I\'m not going to stop you.')
                            await asyncio.sleep(5)
                            check = True
        if check == False:
            await self.bot.send_message(message.author, 'I see. You are not certain about this, are you?')
            await asyncio.sleep(3)
            await self.bot.send_message(message.author, 'Please reconsider. Abandoning what you have done...')
            return check
        await self.bot.send_message(message.author, 'Hello there!\nWelcome to the world of Pokémon!')
        await asyncio.sleep(1.5)
        name = await self.AskName(message)
        naturelist = await self.quiz(message)
        nature = random.choice(naturelist)
        for summary in pmd_json['natures'][nature]['message']:
            #   Last message is formatted differently in the data file
            if summary != pmd_json['natures'][nature]['message'][-1]:
                await bot.send_message(message.author, summary)
                await asyncio.sleep(len(summary)/18)
            else:
                await bot.send_message(message.author, 'So, {0} kind like you...'.format(summary))
                asyncio.sleep(5)
        poke = await self.select_pokemon(message, nature, naturelist)
        stats = self.generate_bst(poke, 5)
        #   Serebii is a current placeholder until I download the assets
        quiz_results = {'name': name, 'id': message.author.id, 'nature': nature, 'species': poke, 'stats': stats,
                        'pfp': 'https://www.serebii.net/supermysterydungeon/pokemon/{0}.png'.format(stats['dex_no']),
                        'joined': time.time()}
        user_data[message.author.id] = quiz_results
        #   Debug
        userwrite()
        await self.send_stats(message, quiz_results)

    async def quiz(self, message):
        questions = self.getPMDquestions(number_of_q)
        await bot.send_message(message.author, 'Now before we begin, I have a few questions.\n'+\
                               'Please answer them truthfully.')
        traits = {}
        for question in questions:
            answers = list(pmd_json['questions'][question].keys())
            options = ['{0}. {1}'.format(answers.index(a)+1, a) for a in answers]
            i = await bot.send_message(message.author, '`'+question+'`\n```'+'\n'.join(options)+\
                                   '```\nPlease answer with a number.\nYou have 12 seconds.')
            t = 12
            response = await bot.wait_for_message(timeout = t, author=message.author, channel = i.channel)
            #   Variable checks for a 'wrong' answer. If
            wrong = False
            sent_wait = True
            sent_wrong = True
            while t > 0:
                if response is None:
                    t -= 6
                    if sent_wait:
                        await bot.send_message(message.author, "Uh, you there?")
                    sent_wait = False
                elif IsInt(response.content) and 0 < int(response.content) <= len(answers):
                    wrong = False
                    break
                else:
                    t -= 4
                    wrong = True
                    if sent_wrong:
                        await bot.send_message(message.author, "Invalid answer, reply with **an available number**!")
                    sent_wrong = False
                    if t>1:
                        response = await bot.wait_for_message(timeout=t, author=message.author, channel=i.channel)
                    else:
                        t = 0
            if t <= 0:
                await bot.send_message(message.author, "*sigh* Fine... let's continue.")
            if response is None and wrong is False:
                #   For people who don't answer at all
                traits = self.traitadd('lazy', traits, 2.01)
            elif wrong:
                traits = self.traitadd('defiant', traits, 2.01)
            else:
                resp = answers[int(response.content)-1]
                assess = pmd_json['questions'][question][resp]
                for trait in list(assess.keys()):
                    traits = self.traitadd(trait, traits, assess[trait])
            await asyncio.sleep(0.8+t/10)
        #   May have multiple "dominant" personalities - so in list instead of a var
        dom = [t.lower() for t in list(traits.keys()) if traits[t] == max(list(traits.values()))]
        return dom

    async def select_pokemon(self, message, nature, naturelist):
        poke = random.choice(pmd_json['natures'][nature]['poke'])
        verdict = await bot.send_message(message.author, 'Should be a {0}!'.format(poke))
        await asyncio.sleep(5)
        await bot.send_message(message.author, 'Alright then, I guess we\'re done here...')
        await asyncio.sleep(1)
        await bot.send_message(message.author, 'Unless you want to be something else?\n(Reply with "Y" to change!)')
        change = await bot.wait_for_message(author=message.author, channel=verdict.channel, timeout = 10)
        if change is not None:
            if change.content.lower().replace('"','').replace("'","") in ['yes', 'y', 'sure', 'ok']:
                options = []
                for sidenature in naturelist:
                    options += pmd_json['natures'][sidenature]['poke']
                    options = list(set(options))
                text_time = 'Alright, these are your options:\n```{0}```\nReply with the name you want. One chance!'\
                .format('\n'.join(options))
                await bot.send_message(message.author, text_time)
                response = await bot.wait_for_message(author=message.author, timeout=5+len(options),
                                                      channel=verdict.channel)
                if response is not None:
                    if response.content.title() in options:
                        poke = response.content.title()
                        await bot.send_message(message.author, 'Alright then, so you\'ll be a {0}!'.format(poke))
        await asyncio.sleep(3)
        await bot.send_message(message.author, 'Well...\nI guess we\'re really done then!')
        return poke

    async def AskName(self, message):
        init = await self.bot.send_message(message.author, "So, before we begin...\nShall we start with your name?")
        await asyncio.sleep(1.5)
        await self.bot.send_message(message.author, "(Please type down your name below)")
        #   "Patience"
        counter = 3
        reply = await self.bot.wait_for_message(timeout = 5, channel = init.channel, author = message.author)
        sent = True
        while reply is None and counter > 0:
            if sent:
                await self.bot.send_message(message.author, "Ahem... I'm waiting...")
            sent = False
            counter -= 1
            reply = await self.bot.wait_for_message(timeout = 10, channel = init.channel, author = message.author)
        if reply is None:
            player_name = message.author.name
        else:
            player_name = reply.content
            await self.bot.send_message(message.author, "I see. So you're **{0}**?\n(Reply with 'N' to change)"\
                                        .format(player_name))
            reply_two = await self.bot.wait_for_message(timeout = 10, channel = init.channel, author = message.author)
            if reply_two is None:
                pass
            elif reply_two.content.lower() not in ["no", "n"]:
                pass
            else:
                await self.bot.send_message(message.author, "Alright, what it is then? I can only take one change...")
                rename = await self.bot.wait_for_message(timeout = 10, channel = init.channel, author = message.author)
                if rename is None:
                    pass
                else:
                    player_name = rename.content
        await self.bot.send_message(message.author, "Very well, we shall go with **{0}** then!".format(player_name))
        await asyncio.sleep(1.5)
        await self.bot.send_message(message.author, "You can change this later, if you wish.")
        return player_name

    async def send_stats(self, message, stats):
        embed = discord.Embed(title="Stats for {0}".format(stats['name']))
        embed.set_thumbnail(url=stats['pfp'])
        embed.add_field(name="Species", value=stats['species'], inline=True)
        embed.add_field(name="Level", value=stats['stats']['level'], inline=True)
        # I should get a subvalue and label it 'stats' as well
        embed.add_field(name="XP", value=str(stats['stats']['stats'][0]), inline=True)
        embed.add_field(name="HP", value=str(stats['stats']['stats'][1]), inline=True)
        embed.add_field(name="Atk", value=str(stats['stats']['stats'][2]), inline=True)
        embed.add_field(name="Def", value=str(stats['stats']['stats'][3]), inline=True)
        embed.add_field(name="SpA", value=str(stats['stats']['stats'][4]), inline=True)
        embed.add_field(name="SpD", value=str(stats['stats']['stats'][5]), inline=True)
        embed.add_field(name="Speed", value=str(stats['stats']['stats'][6]), inline=True)
        embed.add_field(name="Joined at", value =date_time(), inline = False)
        await self.bot.send_message(message.channel, embed=embed)


#   Initiates PMD_module
PMD = PMDModule()


#   Printing message as indicator of readiness
@bot.event
async def on_ready():
    print('Logged in as')
    print(bot.user.name)
    print(bot.user.id)
    print(discord.__version__)
    
#   Main bot part
#   a.k.a. spaghetti section


@bot.event
async def on_message(message):
    #   Long condition line basically:
    #   1. Bot no talking to yourself
    #   2. Ignore non-commands (unless further message in individual commands)
    #   3. Ignore everything outside non-authorized servers
    #   4. DMs are handled differently
    if message.server is not None:
        if message.author.id != bot.user.id and message.content.startswith(';') and \
                (message.server.id in list(data['servers'].keys()) or message.author.id in config.admin_id):
            #   PMD Personality test, after the cooldown and simultaneity test obv
            if message.content == ';pmdquiz':
                if active_commands(';pmdquiz', message.server):
                    perm = await check_cooldown(';pmdquiz', message)
                    if perm[0]:
                        await PMD.personality_test(message)
                else:
                    await bot.send_message(message.author, 'Someone else is taking the quiz, sorry!')
            elif message.content == ';authorize' and message.author.id in config.admin_id:
                await authorize_server(message)
            # Generates help message
            elif message.content in [';help', ';commands', ';command']:
                await help_message(message.author)
            elif message.content.startswith(';pmdstats'):
                if message.author.id in list(user_data.keys()):
                    perm = await check_cooldown(';pmdstats', message)
                    if perm[0]:
                        await PMD.send_stats(message, user_data[message.author.id])
                else:
                    await bot.send_message(message.channel, '{0}, I cannot recognize you. Maybe you should do ;pmdquiz\
                     first before asking about your statistics.'.format(message.author.mention))

#       Runs the whole thing!
bot.run(config.bot_api_key)
