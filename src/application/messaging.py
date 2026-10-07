import re

from discord import Message, Thread

CLOSE_FENCE = "\n```"
INLINE_RE = re.compile(r"`+|\\.|\*\*|__|~~|\|\||\*|_")
MENTION_RE = re.compile(r"\s*<@\d+>\s*")


async def render(thread: Thread, messages: list[Message], text: str) -> None:
    """Spread `text` across `messages`, sending/editing/deleting to fit Discord's limit."""
    chunks = split_message(text)
    for i, chunk in enumerate(chunks):
        if i >= len(messages):
            messages.append(await thread.send(chunk))
        elif messages[i].content != chunk:
            messages[i] = await messages[i].edit(content=chunk)
    for m in messages[len(chunks) :]:
        await m.delete()
    del messages[len(chunks) :]


def _open_formatting(chunk: str) -> tuple[str | None, list[str], bool]:
    """Return the open code fence line, open inline markers and >>> quote state."""
    fence: str | None = None
    stack: list[str] = []
    block_quote = False
    for line in chunk.split("\n"):
        if line.startswith("```"):
            fence = None if fence else line
            stack.clear()
            continue
        if fence:
            continue
        if line.startswith(">>> "):
            block_quote = True
        for m in INLINE_RE.finditer(line):
            tok = m.group()
            if stack and stack[-1][0] == "`":
                if tok == stack[-1]:
                    stack.pop()
                continue
            if tok[0] == "\\":
                continue
            if tok[0] == "`":
                stack.append(tok)
                continue
            before = line[m.start() - 1] if m.start() else " "
            after = line[m.end()] if m.end() < len(line) else " "
            # Discord's rules, approximately: `*`/`**` must hug the text they wrap
            # (so bullets and `a * b` don't count) and `_` must not sit inside a word
            if (
                tok in stack
                and not before.isspace()
                and not (tok == "_" and after.isalnum())
            ):
                del stack[len(stack) - 1 - stack[::-1].index(tok)]
            elif not after.isspace() and not (tok == "_" and before.isalnum()):
                stack.append(tok)
    return fence, stack, block_quote


def split_message(text: str, limit: int = 2000) -> list[str]:
    """Split `text` into chunks <= `limit`, preferring paragraph/line/word breaks.

    Formatting left open at a cut (code blocks, inline markers, quotes) is closed
    at the end of the chunk and reopened at the start of the next one.
    """
    chunks: list[str] = []
    reopen = ""
    while text:
        text = reopen + text
        if len(text) <= limit:
            chunks.append(text)
            break
        # Start past `reopen` so a cut always makes progress
        start = len(reopen) + 1
        budget = limit
        while True:
            for sep in ("\n\n", "\n", " "):
                cut = text.rfind(sep, start, budget)
                if cut != -1:
                    break
            else:
                sep, cut = "", budget
            chunk = text[:cut]
            fence, stack, block_quote = _open_formatting(chunk)
            if fence:
                suffix = CLOSE_FENCE
            elif stack:
                chunk = chunk.rstrip()
                suffix = "".join(reversed(stack))
            else:
                suffix = ""
            if len(chunk) + len(suffix) <= limit:
                break
            budget = min(budget - 1, limit - len(suffix))

        last_line = chunk.rsplit("\n", 1)[-1]
        if block_quote:
            reopen = ">>> "
        elif sep in (" ", "") and last_line.startswith("> "):
            reopen = "> "
        else:
            reopen = ""
        reopen += f"{fence}\n" if fence else "".join(stack)

        chunks.append(chunk + suffix)
        text = text[cut + len(sep) :]
    return chunks


def strip_mentions(text: str) -> str:
    return re.sub(MENTION_RE, "", text)
