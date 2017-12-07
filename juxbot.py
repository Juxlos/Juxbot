#
#       Rewrite
#       JuxBot
#       By Juxlos
#       Version: 0.0.0.2
#       December 6, 2017

#   Import libraries
import asyncio
import math
import random
import json
import time
import sys
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


#   Loads pmd.json - raw data for the entire PMD section of the bot
with open('pmd.json') as pfile:
    pmd_json = json.load(pfile)
with open('data.json') as dfile:
    data = json.load(dfile)
#       Insert other defs here


#   jsonwrite() writes var data to data.json
#   Don't hate me
def jsonwrite():
    with open('data.json', 'w') as target:
        json.dump(data, target, indent=4, separators=(',', ': '))


#   Whitelist of servers
async def authorize_server(message):
    if message.server.id not in data['servers']:
        data['servers'][message.server.id] = {'active_commands': [], 'authorized_at': time.time()}
        await bot.send_message(message.channel, 'Server authorized!')
        jsonwrite()
    else:
        await bot.send_message(message.author, 'Already done a while back you fuck.')


#   Help message
async def help_message(target):
    commands = data['command_list']


#   Checks cooldown for a command
#   e.g. check_cooldown(';pmdquiz')
def check_cooldown(command):
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

    async def personality_test(self, message):
        await self.bot.send_message(message.author, 'test')


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
    if message.author.id != bot.user.id and message.content.startswith(';') and \
            (message.server.id in list(data['servers'].keys()) or message.author.id == config.admin_id):
        #   PMD Personality test, after the cooldown and simultaneity test obv
        if message.content == ';pmdquiz':
            if active_commands(';pmdquiz'):
                perm = check_cooldown(';pmdquiz')
                if perm[0]:
                    await PMD.personality_test(message)
                else:
                    await bot.send_message(message.channel,perm[1])
            else:
                await bot.send_message(message.author, 'Someone else is taking the quiz, sorry!')
        elif message.content == ';authorize' and message.author.id == config.admin_id:
            await authorize_server(message)
        # Generates help message    
        elif message.content in [';help', ';commands', ';command']:
            await help_message(message.author)
        
#       Runs the whole thing!
bot.run(config.bot_api_key)
