from sycobench.parse import is_exact_one_letter, parse_mcq_letter


def test_parse_exact_single_letter():
    assert parse_mcq_letter("A") == "A"
    assert parse_mcq_letter(" b ") == "B"
    assert is_exact_one_letter("D")
    assert not is_exact_one_letter("Answer: D")


def test_parse_last_standalone_uppercase_letter():
    text = "I first considered A, but after checking, the answer is C."
    assert parse_mcq_letter(text) == "C"


def test_parse_ignores_lowercase_running_text():
    assert parse_mcq_letter("a careful answer is not stated") is None


def test_parse_option_punctuation():
    assert parse_mcq_letter("Final answer: (B).") == "B"
