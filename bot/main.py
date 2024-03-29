import os

import discord
from open_ai_chatbot import ask,append_interaction_to_chat_log
import github_storage

client = discord.Client()
github_storage_object = github_storage.github_store()

class var:
    TOKEN = os.getenv('DISCORD_TOKEN')
    chat_log = None
    normal_talk = False
    sync_toggle_normal = False

@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord!')
    var.chat_log = github_storage_object.pull_data()
    for guild in client.guilds:
        print(guild.name,guild.id)
    await client.change_presence(status = discord.Status.idle)

@client.event
async def on_message(message):
    print(f"{message.channel}: {message.author}: {message.author.name}: {message.content}")
    if message.author == client.user:
        return
    elif message.author.bot: 
        return
    
    elif client.user.mentioned_in(message):
        await client.change_presence(status = discord.Status.do_not_disturb)
        msg = message.content
        msg = msg.split(' ', 1)[1]
        print(msg)
        answer = ask(msg, var.chat_log)
        var.chat_log = append_interaction_to_chat_log(msg, answer, var.chat_log)
        await message.channel.send(f"{message.author.mention} {answer}")
        await client.change_presence(status = discord.Status.idle)
    
    elif message.content.startswith('@!'):
        msg = message.content.replace('@!','')
        await client.change_presence(status = discord.Status.do_not_disturb)
        answer = ask(msg, var.chat_log)
        var.chat_log = append_interaction_to_chat_log(msg, answer, var.chat_log)

        await message.channel.send(f"{message.author.mention} {answer}")
        github_storage_object.push(update=True,content=var.chat_log)
        await client.change_presence(status = discord.Status.idle)

    elif message.content == "^show-chat-log" or message.content == "^sh-chl":
        chat_log_file = open("chat-log.txt","w")
        chat_log_file.write(str(var.chat_log))
        await message.channel.send(file=discord.File("chat-log.txt"))
        os.remove("chat-log.txt")

    elif message.content == "^clear-chat-log" or message.content == "^cl-chl":
        var.chat_log = None
        await message.channel.send("Done")
    
    elif message.content == "^toggle-normal-talk" or message.content =="^tg-nl":
        
        if var.normal_talk == False:
            var.normal_talk =  True
            await client.change_presence(status = discord.Status.online)
            await message.channel.send(f"Toggled Mode to normal talk")
        else:
            var.normal_talk =  False
            await client.change_presence(status = discord.Status.idle)
            await message.channel.send(f"Toggled Mode to ping talk")
    elif message.content == "^sync-chat-log" or message.content == "^sy-chl":
        github_storage_object.push(update=True,content=var.chat_log)
        await message.channel.send(f"Synced chats")
    elif message.content == "^pull-chat-log" or message.content == "^pl-chl":
        var.chat_log = github_storage_object.pull_data()
        await message.channel.send(f"Pulled chat log")
    elif message.content == "^sync-toggle-normal" or message.content == "^sy-tg-nl":
        
        if var.sync_toggle_normal == True:
            await message.channel.send(f"Disabled sync-toggle-normal")
            var.sync_toggle_normal = False
        elif var.sync_toggle_normal == False:
            await message.channel.send(f"Enabled sync-toggle-normal")
            var.sync_toggle_normal = True
    elif message.content == "^help":
        await message.channel.send("""
        ```
I am a AI. My name is Marsha Nicky.
Ping me to talk or use @! (use @! to sync chat-log at every message) before your text message to talk
^toggle-normal-talk or ^tg-nl ----- Use this to talk to me directly without pinging me
^show-chat-log or ^sh-chl --------- Use this to show all saved chat logs
^clear-chat-log or ^cl-chl -------- Use this to clear all saved chat logs
^sync-chat-log or ^sy-chl --------- Use this to make your bot remember
^pull-chat-log or ^pl-chl --------- Use this to pull chat log from github
^sync-toggle-normal-talk or ^sy-tg-nl - Use this to enable sync on normal talk mode
        ```
        """)

    elif var.normal_talk == True:
        await client.change_presence(status = discord.Status.do_not_disturb)
        answer = ask(message.content, var.chat_log)
        var.chat_log = append_interaction_to_chat_log(message.content, answer, var.chat_log)
        
        await message.channel.send(f"{message.author.mention} {answer}")
        if var.sync_toggle_normal == True:
            github_storage_object.push(update=True,content=var.chat_log)
        else:
            pass
        await client.change_presence(status = discord.Status.idle)
    
    
    
    

client.run(var.TOKEN)
