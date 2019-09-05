#!/usr/bin/env python3
import discord
import asyncio
import aiohttp
import json

import youtube_dl 
import sys
import os
from os import path
import re
import time

from discord.ext import commands

TOKEN = 'NTM0NDk2NTI2NjM0OTc1MjYy.Dx7TKA.kIFtxiQ0m0C_S1hGVdhU_eiS9LE'

client = commands.Bot(command_prefix = '!!')
players = {}
downloadInfo = []

@client.event
async def on_ready():
    print('Logged in as:')
    print(client.user.name)
    print(client.user.id)
    print('-------------')
    print('Bot is ready.')
    print('-------------') 

@client.command()
async def echo(*args): 
   output = ''
   for word in args:
       output += str(word)
       output += ' '
   await client.say(output)

@client.event
async def on_message(message):     
    await client.process_commands(message)

@client.command(pass_context=True)
async def clear(ctx, amount=100):
    channel = ctx.message.channel
    messages = []
    async for message in client.logs_from(channel, limit=int(amount)):
        messages.append(message)
    await client.delete_messages(messages)
    await client.say('Messages deleted')

class Logs(object):
    def debug(self, msg):
        pass
    def warning(self, msg):
        pass
    def error(self, msg):
        print(msg)


@client.command(pass_context=True)
async def dl(ctx, args):
    print('____________________________')
    print('Downloading Command Entered:')
    print('____________________________')
    channel = ctx.message.channel
    failed = False
    result = None

    def status(d):
        if d['status'] == 'finished':
            print('Done downloading, now converting ...')
            #downloadInfo.append('Done downloading, now converting ...')
        if d['status'] == 'downloading':
            percentage = ((d['downloaded_bytes'] / d['total_bytes']) * 100)
            output = "Download %.2f %% completed" % percentage
            print(output)
            #downloadInfo.append(output)

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': '%(title)s.mp3',
        'quiet': True,
        'logger': Logs(),
        'progress_hooks': [status],
    }

    try:
        URL = str(args)
        if 'list' in URL:
            await client.say("Cannot process playlists."\
                             " Enter a single video to download")
            return
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            result = ydl.extract_info(URL, download=False)
            fileSize = result.get('filesize', None)
            print('FileSize: ' + str(fileSize))
            if fileSize > 8388608:
                await client.say('This file is too large to download. '\
                                 'Try a shorter video')
                print('File too large to download')
                failed = True
            else:
                await client.say("Downloading your song...")
                print("Downloading...")
                ydl.download([URL])
    except Exception as e:
        await client.say(e)
        pass

    '''
    Optional to show download progress
    '''
    # for percent in downloadInfo:
    #    await client.say(str(percent))
    if not failed:
        fileName = ydl.prepare_filename(result)
        await client.say('Download Finished!\nNow Converting...')

    # Try to remove the file
    try:
        print("Attempting to remove files")

        size = os.stat(fileName)
        print('FileSize: ' + str(size.st_size))
        if int(str(size.st_size)) > 8388608:
            await client.say('File is too large to upload. '\
                             'Try a shorte video')
            print('File too large to download')
        else:
            if '.m4a' in str(fileName):
                fileName = fileName[:-3] + '.mp3'
            else:
                fileName = fileName[:-4] + '.mp3'

        await client.send_file(channel, fileName, filename=str(fileName),\
                               content='Here is your download:')
        os.remove(fileName)
        print('File was successfully removed: \n' + fileName)
    except FileNotFoundError as e:
        print('\nError removing the file: ' + fileName)
        print(e)


'''
@client.command(pass_context=True)
async def leave(ctx):
    server = ctx.message.server
    channel = ctx.message.author.voice.voice_channel
    voice_client = client.voice_client_in(server)  
    await voice_client.disconnect()
'''


@client.command(pass_context=True)
async def stop(ctx):
    id = ctx.message.server.id
    players[id].stop()


@client.command(pass_context=True)
async def pause(ctx):
    server = ctx.message.server
    channel = ctx.message.author.voice.voice_channel
    botChannel = client.voice_client_in(server)
    id = ctx.message.server.id
    await client.say('Pausing...')
    players[id].pause()


@client.command(pass_context=True)
async def resume(ctx):
    server = ctx.message.server
    channel = ctx.message.author.voice.voice_channel
    id = ctx.message.server.id
    
    if channel == None:
        await client.say('Bot must be playing in a channel')
    else: 
        if not players[id].is_playing():
            await client.say('Resuming the music...')
            print('Resuming the music.')
            voice_client = client.voice_client_in(server)  
            await voice_client.move_to(channel)
            players[id].resume()
        else:
            await client.say('The bot is already playing music')


@client.command(pass_context=True)
async def play(ctx, url):
    server = ctx.message.server
    author = ctx.message.author 
    voice_channel = author.voice.voice_channel 
    channel = None
    
    try:
        if voice_channel != None:
            channel = voice_channel.name 
            await client.say("User who requested the bot to be played: " + str(author) +\
                             "\nThey are in the channel: " + channel)
            await client.say('Please wait while the music is prepared.')
            
            if os.path.isfile('song.mp3'):
                os.remove('song.mp3')

            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'outtmpl': 'song.mp3',
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url]) 

            vc = await client.join_voice_channel(voice_channel)
            player = vc.create_ffmpeg_player('song.mp3', after=lambda: print('done'))
            players[server.id] = player
            player.start()
            player.volume = .5
            
            while not player.is_done():
                await asyncio.sleep(1)
            
            #player.stop()
            os.remove('song.mp3')
            await vc.disconnect()
        else:
            await client.say("User is not in a channel")
    except Exception as e:
        await client.say(e)

    
    '''
    server = ctx.message.server
    voice_client = client.voice_client_in(server)
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': 'song.mp3',
    }
    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([url])

    if voice_client and voice_client.is_connected():
        await voice_client.move_to(channel)
    else:
        voice_client = await channel.connect()

    voice_client.play(discord.FFmpegPCMAudio('song.mp3'), after=lambda e: print('done', e))
    voice_client.is_playing()
    voice_client.source = discord.PCMVolumeTransformer(voice_client.source)
    voice_client.source.volume = 0.5
    await ctx.message.delete()

#Have to fix this
@client.command()
async def ping(ctx):
    ping_ = client.latency
    ping = round(ping_ * 1000)
    await ctx.send('Your ping is {0}ms'.format(ping))
'''

@client.command()
async def btc():
    url = 'https://api.coindesk.com/v1/bpi/currentprice/BTC.json'
    async with aiohttp.ClientSession() as session:  # Async HTTP request
        raw_response = await session.get(url)
        response = await raw_response.text()
        response = json.loads(response)
        await client.say("Bitcoin price is: $" + response['bpi']['USD']['rate'])

client.run(TOKEN)
