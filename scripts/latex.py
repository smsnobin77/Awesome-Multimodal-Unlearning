"""LaTeX and BibTeX helpers for reading the survey sources."""

import re
from pathlib import Path

from pylatexenc.latex2text import LatexNodes2Text

_L2T = LatexNodes2Text()
_LABEL = re.compile(r"\\textbf\{([^{}]*?)\.\}")
_HEADING = re.compile(r"\\(?:sub)*section\*?\{([^{}]*)\}")
_CITE = re.compile(r"~?\\cite\w*\*?(?:\[[^\]]*\])*\{([^}]*)\}")


def live(path: Path) -> str:
    text = re.sub(r"\\iffalse.*?\\fi\b", "", Path(path).read_text(), flags=re.S)
    return "\n".join(line for line in text.split("\n") if not line.lstrip().startswith("%"))


def plain(s: str) -> str:
    s = s.replace("$_2$", "2").replace("\u2011", "-")
    return re.sub(r"\s+", " ", _L2T.latex_to_text(s)).strip()


def norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def cite_keys(text: str) -> list[str]:
    return [k.strip() for m in _CITE.finditer(text) for k in m.group(1).split(",") if k.strip()]


def strip_cites(text: str) -> str:
    return _CITE.sub("", text)


def _braced(text: str, start: int) -> tuple[str, int]:
    depth = 0
    for i in range(start, len(text)):
        depth += {"{": 1, "}": -1}.get(text[i], 0)
        if depth == 0:
            return text[start + 1 : i], i + 1
    raise ValueError("unbalanced braces")


def parse_bib(text: str) -> dict[str, dict]:
    field_re, value_re, sep_re = re.compile(r"\s*(\w+)\s*=\s*"), re.compile(r"[\w.-]+"), re.compile(r"\s*,?")
    entries = {}
    for m in re.finditer(r"@(\w+)\s*\{\s*([^,\s]+)\s*,", text):
        if m.group(1).lower() in {"comment", "string", "preamble"}:
            continue
        body, end = _braced(text, text.index("{", m.start()))
        fields, pos = {}, body.index(",") + 1
        while f := field_re.match(body, pos):
            if f.end() >= len(body):
                break
            if body[f.end()] == "{":
                value, pos = _braced(body, f.end())
            elif body[f.end()] == '"':
                close = body.index('"', f.end() + 1)
                value, pos = body[f.end() + 1 : close], close + 1
            else:
                v = value_re.match(body, f.end())
                value, pos = v.group(0), v.end()
            fields[f.group(1).lower()] = value
            pos = sep_re.match(body, pos).end()
        entries[m.group(2)] = {"type": m.group(1).lower(), "fields": fields, "raw": text[m.start() : end].strip()}
    return entries


def labeled_paragraphs(text: str) -> list[tuple[str, str]]:
    marks = list(_LABEL.finditer(text))
    stops = [m.start() for m in _HEADING.finditer(text)] + [len(text)]
    out = []
    for i, m in enumerate(marks):
        nxt = marks[i + 1].start() if i + 1 < len(marks) else len(text)
        end = min([s for s in stops if s > m.end()] + [nxt])
        out.append((plain(m.group(1)), text[m.end() : end]))
    return out


def subsections(text: str) -> list[tuple[str, str]]:
    heads = list(re.finditer(r"\\subsection\*?\{([^{}]*)\}", text))
    return [(plain(h.group(1)), text[h.end() : heads[i + 1].start() if i + 1 < len(heads) else len(text)])
            for i, h in enumerate(heads)]


def display_math(text: str) -> list[str]:
    return [norm_ws(m.replace("\\nonumber", "").replace("\\mbox{", "\\text{")) for m in re.findall(r"\\\[(.*?)\\\]", text, re.S)]


def first_sentence(latex: str) -> str:
    text = plain(strip_cites(re.sub(r"\\\[.*?\\\]", " ", latex, flags=re.S)))
    m = re.match(r"(.+?[.!?])(\s|$)", text)
    return m.group(1) if m else text
