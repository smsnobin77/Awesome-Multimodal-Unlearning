from import_survey import short_venue


def test_workshop_papers_keep_the_word_workshop():
    assert short_venue("ICML 2025 Workshop on Machine Unlearning for Generative AI") == "ICML Workshop"
    assert short_venue("International Conference on Machine Learning") == "ICML"
