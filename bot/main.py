"""Marsha Nicky - an AI chat bot for Discord.

Environment: DISCORD_TOKEN, OPENAI_API_KEY (required); GITHUB_TOKEN +
MEMORY_REPO to persist memory (optional); OWNER_ID (optional, your Discord
user ID, can always run admin commands).

Enable the "Message Content" privileged intent for the bot in the Discord
developer portal, otherwise it can't read messages.
"""

import asyncio
import logging
import os
import sys

import discord

from brain import Brain

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("marsha")

TOKEN = os.getenv("DISCORD_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0") or 0)
DISCORD_LIMIT = 2000

HELP = """```
I am an AI. My name is Marsha Nicky.
Mention me, or start a message with @! to talk to me.
^toggle-normal-talk  (^tg-nl)  talk without pinging me in this channel
^show-chat-log       (^sh-chl) show what I remember in this channel  [mods]
^clear-chat-log      (^cl-chl) forget this channel's conversation    [mods]
^sync-chat-log       (^sy-chl) save memory to GitHub                 [mods]
^pull-chat-log       (^pl-chl) load memory from GitHub               [mods]
```"""

intents = discord.Intents.default()
intents.message_content = True  # required since 2022 to read message text
client = discord.Client(intents=intents)
brain = Brain()
normal_talk_channels: set[int] = set()
storage = None


def get_storage():
    global storage
    if storage is None and os.getenv("GITHUB_TOKEN"):
        from github_storage import github_store
        storage = github_store()
    return storage


def is_moderator(message: discord.Message) -> bool:
    """Admin commands used to work for anyone in any server."""
    if OWNER_ID and message.author.id == OWNER_ID:
        return True
    permissions = getattr(message.channel, "permissions_for", None)
    return bool(permissions and permissions(message.author).manage_messages)


def split(text: str, limit: int = DISCORD_LIMIT - 100) -> list[str]:
    return [text[i:i + limit] for i in range(0, len(text), limit)] or ["…"]


async def reply(message: discord.Message, question: str) -> None:
    question = question.strip()
    if not question:
        await message.channel.send(f"{message.author.mention} yes? 🙂")
        return
    async with message.channel.typing():
        try:
            answer = await brain.ask(message.channel.id, message.author.display_name, question)
        except Exception:
            log.exception("OpenAI request failed")
            answer = "Sorry, my brain glitched. Try again in a moment."
    for i, chunk in enumerate(split(answer)):
        await message.channel.send(f"{message.author.mention} {chunk}" if i == 0 else chunk)


async def sync_memory() -> bool:
    store = get_storage()
    if not store:
        return False
    await asyncio.to_thread(store.push, brain.export())
    return True


@client.event
async def on_ready():
    log.info("%s connected to %d server(s)", client.user, len(client.guilds))
    store = get_storage()
    if store:
        try:
            brain.load(await asyncio.to_thread(store.pull_data))
        except Exception:
            log.exception("Couldn't load memory from GitHub")
    await client.change_presence(status=discord.Status.idle)


ADMIN = {
    ("^show-chat-log", "^sh-chl"): "show",
    ("^clear-chat-log", "^cl-chl"): "clear",
    ("^sync-chat-log", "^sy-chl"): "sync",
    ("^pull-chat-log", "^pl-chl"): "pull",
}


@client.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    content = message.content.strip()

    if content == "^help":
        await message.channel.send(HELP)
        return

    if content in ("^toggle-normal-talk", "^tg-nl"):
        if message.channel.id in normal_talk_channels:
            normal_talk_channels.discard(message.channel.id)
            await message.channel.send("Toggled mode to ping talk")
        else:
            normal_talk_channels.add(message.channel.id)
            await message.channel.send("Toggled mode to normal talk in this channel")
        return

    for aliases, action in ADMIN.items():
        if content in aliases:
            if not is_moderator(message):
                await message.channel.send("Only moderators can do that.")
                return
            if action == "show":
                await message.channel.send(f"```\n{brain.transcript(message.channel.id)[-1800:]}\n```")
            elif action == "clear":
                brain.clear(message.channel.id)
                await message.channel.send("Done, I forgot this channel's conversation.")
            elif action == "sync":
                ok = await sync_memory()
                await message.channel.send("Synced memory" if ok else "GitHub storage isn't configured.")
            elif action == "pull":
                store = get_storage()
                if store:
                    brain.load(await asyncio.to_thread(store.pull_data))
                await message.channel.send("Pulled memory" if store else "GitHub storage isn't configured.")
            return

    if client.user in message.mentions:
        question = content.replace(f"<@{client.user.id}>", "").replace(f"<@!{client.user.id}>", "")
        await reply(message, question)
    elif content.startswith("@!"):
        await reply(message, content[2:])
        try:
            await sync_memory()
        except Exception:
            log.exception("Memory sync failed")
    elif message.channel.id in normal_talk_channels:
        await reply(message, content)


if __name__ == "__main__":
    if not TOKEN or not os.getenv("OPENAI_API_KEY"):
        sys.exit("Set DISCORD_TOKEN and OPENAI_API_KEY.")
    client.run(TOKEN, log_handler=None)
