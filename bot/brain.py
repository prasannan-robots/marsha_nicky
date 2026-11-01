"""Conversation memory and replies for Marsha Nicky."""

import os
from collections import defaultdict, deque

from openai import AsyncOpenAI

MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
MAX_TURNS = int(os.getenv("MEMORY_TURNS", "20"))  # exchanges remembered per channel
PERSONA = os.getenv(
    "BOT_PERSONA",
    "You are Marsha Nicky, a friendly, witty AI hanging out in a Discord server. "
    "Keep replies short and conversational (under 1500 characters).",
)


class Brain:
    """Keeps a rolling window of recent exchanges per Discord channel, so one
    server's conversations never leak into another's."""

    def __init__(self, client=None):
        self.client = client
        self.history = defaultdict(lambda: deque(maxlen=MAX_TURNS * 2))

    def _client(self):
        if self.client is None:
            self.client = AsyncOpenAI()
        return self.client

    async def ask(self, channel_id: int, author: str, question: str) -> str:
        memory = self.history[channel_id]
        messages = [{"role": "system", "content": PERSONA}, *memory,
                    {"role": "user", "content": f"{author}: {question}"}]
        response = await self._client().chat.completions.create(model=MODEL, messages=messages,
                                                                 max_completion_tokens=400)
        answer = (response.choices[0].message.content or "").strip() or "…"
        memory.append({"role": "user", "content": f"{author}: {question}"})
        memory.append({"role": "assistant", "content": answer})
        return answer

    def transcript(self, channel_id: int) -> str:
        return "\n".join(f"{m['role']}: {m['content']}" for m in self.history[channel_id]) or "(empty)"

    def clear(self, channel_id: int) -> None:
        self.history.pop(channel_id, None)

    def export(self) -> dict:
        return {str(cid): list(turns) for cid, turns in self.history.items() if turns}

    def load(self, data: dict) -> None:
        for cid, turns in (data or {}).items():
            self.history[int(cid)] = deque(turns[-MAX_TURNS * 2:], maxlen=MAX_TURNS * 2)
