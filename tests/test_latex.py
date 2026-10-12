from latex import (cite_keys, display_math, first_sentence, labeled_paragraphs, live, parse_bib, plain,
                   slug, subsections)


def test_live_drops_comments_and_iffalse(tmp_path):
    f = tmp_path / "a.tex"
    f.write_text("keep\n  % gone\n\\iffalse hidden \\fi\nalso keep")
    assert live(f) == "keep\n\nalso keep"


def test_plain_handles_subscript_and_nonbreaking_hyphen():
    assert plain("CO$_2$e") == "CO2e"
    assert plain("VLM\u2011Based") == "VLM-Based"


def test_cite_keys_reads_all_cite_forms():
    text = r"A~\cite{a, b} and \citealp{c} and \citep{a}"
    assert cite_keys(text) == ["a", "b", "c", "a"]


def test_parse_bib_braced_and_quoted():
    bib = '@article{k1,\n title = {A {B} c},\n year = 2024,\n note = "x y"\n}\n@inproceedings{k2, title={T}}'
    out = parse_bib(bib)
    assert out["k1"]["fields"] == {"title": "A {B} c", "year": "2024", "note": "x y"}
    assert out["k2"]["type"] == "inproceedings"


def test_labeled_paragraphs_split_on_bold_labels_and_headings():
    text = r"\textbf{intro words} x \textbf{One.} first~\cite{a}. \textbf{Two.} second \subsection{S} tail"
    assert [(lab, body.strip()) for lab, body in labeled_paragraphs(text)] == [
        ("One", r"first~\cite{a}."), ("Two", "second")]


def test_subsections_and_math_and_first_sentence():
    text = "\\subsection{Alpha}\nBody one.\n\\[ x = 1 \\nonumber \\]\n\\subsection{Beta}\nBody two."
    assert [t for t, _ in subsections(text)] == ["Alpha", "Beta"]
    assert display_math(text) == ["x = 1"]
    assert first_sentence(r"Methods edit inputs~\cite{a}, not weights. More text.") == "Methods edit inputs, not weights."


def test_slug():
    assert slug("FA@K") == "fa-k" and slug("CO2e") == "co2e" and slug("Top-k Acc") == "top-k-acc"
