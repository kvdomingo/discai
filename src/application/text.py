from textwrap import dedent


def normalize_text(text: str) -> str:
    return dedent(text).strip()
