import asyncio
import os
import sys
from types import SimpleNamespace

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "bot"))
os.environ.setdefault("MEMORY_TURNS", "2")
import brain as brain_module  # noqa: E402
import main  # noqa: E402


class FakeCompletions:
    def __init__(self):
        self.calls = []

    async def create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=f"reply {len(self.calls)}"))])


def fake_brain():
    completions = FakeCompletions()
    return brain_module.Brain(client=SimpleNamespace(chat=SimpleNamespace(completions=completions))), completions


def test_memory_is_per_channel_and_trimmed():
    b, completions = fake_brain()
    for i in range(5):
        asyncio.run(b.ask(1, "asha", f"q{i}"))
    asyncio.run(b.ask(2, "ravi", "hello"))
    # channel 2's prompt contains nothing from channel 1
    assert all("q" not in m["content"] for m in completions.calls[-1]["messages"][1:-1])
    assert len(b.history[1]) == 4  # MEMORY_TURNS=2 exchanges
    restored = brain_module.Brain()
    restored.load(b.export())
    assert list(restored.history[1]) == list(b.history[1])


class FakeChannel:
    def __init__(self, cid=10, manage=False):
        self.id, self.sent, self.manage = cid, [], manage

    async def send(self, text):
        self.sent.append(text)

    def typing(self):
        class _T:
            async def __aenter__(s): return s
            async def __aexit__(s, *a): return False
        return _T()

    def permissions_for(self, member):
        return SimpleNamespace(manage_messages=self.manage)


def message(content, channel, author_id=5, mentions=()):
    author = SimpleNamespace(id=author_id, bot=False, mention=f"<@{author_id}>", display_name="Asha")
    return SimpleNamespace(content=content, channel=channel, author=author, mentions=list(mentions))


def run(msg, monkeypatch):
    b, _ = fake_brain()
    monkeypatch.setattr(main, "brain", b)
    me = SimpleNamespace(id=99)
    monkeypatch.setattr(main, "client", SimpleNamespace(user=me))
    asyncio.run(main.on_message(msg))
    return b


def test_admin_commands_need_moderator(monkeypatch):
    ch = FakeChannel(manage=False)
    run(message("^show-chat-log", ch), monkeypatch)
    assert ch.sent == ["Only moderators can do that."]
    mod = FakeChannel(manage=True)
    run(message("^clear-chat-log", mod), monkeypatch)
    assert "forgot" in mod.sent[0]


def test_mention_and_bare_mention(monkeypatch):
    me = SimpleNamespace(id=99)
    ch = FakeChannel()
    run(message("<@99> how are you?", ch, mentions=[me]), monkeypatch)
    assert ch.sent == ["<@5> reply 1"]
    ch2 = FakeChannel()
    run(message("<@99>", ch2, mentions=[me]), monkeypatch)  # used to raise IndexError
    assert "yes?" in ch2.sent[0]


def test_long_replies_are_split():
    assert all(len(c) <= 1900 for c in main.split("x" * 5000))
