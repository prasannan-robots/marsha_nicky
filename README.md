# Marsha Nicky — Discord bot

An AI chat bot for Discord powered by OpenAI. It remembers the recent conversation in each
channel separately and can save that memory to a GitHub repository.

## Setup

1. Create a bot in the [Discord developer portal](https://discord.com/developers/applications),
   enable the **Message Content Intent** (Bot → Privileged Gateway Intents) and invite it.
2. Set environment variables:

   | Variable | Required | Purpose |
   | --- | --- | --- |
   | `DISCORD_TOKEN` | yes | Bot token |
   | `OPENAI_API_KEY` | yes | OpenAI key |
   | `OPENAI_MODEL` | no | default `gpt-4o-mini` |
   | `OWNER_ID` | no | Your Discord user ID (can always run admin commands) |
   | `GITHUB_TOKEN`, `MEMORY_REPO` | no | Save memory as `memory.json` in that repo |
   | `MEMORY_TURNS` | no | Exchanges remembered per channel (default 20) |

3. `pip install -r requirements.txt && python bot/main.py`

## Commands

- Mention the bot, or start a message with `@!` to talk (and save memory).
- `^tg-nl` — talk without pinging in the current channel.
- `^sh-chl`, `^cl-chl`, `^sy-chl`, `^pl-chl` — show / clear / save / load memory
  (needs *Manage Messages* or `OWNER_ID`).
- `^help`
