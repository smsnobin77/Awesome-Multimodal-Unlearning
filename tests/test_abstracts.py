from abstracts import openalex_text, similar


def test_similar_titles():
    assert similar("SalUn: Empowering Machine Unlearning", "Salun: empowering machine unlearning")
    assert not similar("SalUn: Empowering Machine Unlearning", "Denoising diffusion models")


def test_openalex_inverted_index():
    assert openalex_text({"hello": [0, 2], "world": [1]}) == "hello world hello"
