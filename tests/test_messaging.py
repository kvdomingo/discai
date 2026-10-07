from src.application.messaging import _open_formatting, split_message


def assert_well_formed(chunks: list[str], limit: int = 2000) -> None:
    for c in chunks:
        assert len(c) <= limit
        fence, stack, _ = _open_formatting(c)
        assert fence is None and stack == [], c


def squash(s: str) -> str:
    return "".join(s.split())


def test_short():
    assert split_message("") == []
    assert split_message("hi") == ["hi"]


def test_prose_keeps_every_word():
    prose = "\n\n".join(["word " * 100] * 10)
    out = split_message(prose)
    assert len(out) > 1
    assert_well_formed(out)
    assert squash("".join(out)) == squash(prose)


def test_no_whitespace():
    out = split_message("a" * 5000)
    assert_well_formed(out)
    assert "".join(out) == "a" * 5000


def test_code_block_reopens_with_language():
    code = "intro\n```py\n" + "\n".join(f"x = {i}" for i in range(500)) + "\n```\nend"
    out = split_message(code)
    assert len(out) > 1
    assert_well_formed(out)
    assert all(c.startswith("```py\n") for c in out[1:-1])


def test_inline_markers_reopen():
    for marker in ("**", "*", "__", "_", "~~", "||", "`"):
        out = split_message(f"{marker}{'word ' * 600}end{marker}")
        assert len(out) > 1
        assert_well_formed(out)
        assert all(c.startswith(marker) for c in out[1:]), marker


def test_nested_markers_close_in_reverse():
    out = split_message(f"**bold ~~strike {'word ' * 600}end~~**")
    assert_well_formed(out)
    assert out[0].endswith("~~**")
    assert out[1].startswith("**~~")


def test_non_formatting_symbols_ignored():
    for text in ("snake_case " * 400, "* item\n" * 500, "2 * 3 = 6\n" * 300):
        out = split_message(text)
        assert_well_formed(out)
        assert squash("".join(out)) == squash(text)


def test_escaped_marker_ignored():
    out = split_message(r"\*" + "word " * 600)
    assert not out[1].startswith("*")


def test_block_quote_reopens():
    out = split_message(">>> " + "word " * 600)
    assert len(out) > 1
    assert all(c.startswith(">>> ") for c in out)


def test_line_quote_reopens_on_mid_line_cut():
    out = split_message("> " + "word " * 600)
    assert all(c.startswith("> ") for c in out)
