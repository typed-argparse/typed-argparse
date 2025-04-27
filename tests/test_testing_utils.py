from ._testing_utils import remove_ansii_escape_sequences


def test_remove_ansii_escape_sequences() -> None:
    assert remove_ansii_escape_sequences("foo") == "foo"
    assert remove_ansii_escape_sequences("\x1b[90m") == ""
    assert remove_ansii_escape_sequences("\x1B[90m") == ""
    assert remove_ansii_escape_sequences("\x1B[90mfoo") == "foo"
    try:
        from yachalk import chalk  # pyright: ignore

        yachalk_string = chalk.gray("foobar")
    except ImportError:
        yachalk_string = "foobar"
    assert remove_ansii_escape_sequences(yachalk_string) == "foobar"
    sample_with_ansii = "Some epsilon \x1b[90m[default: 0.1]\x1b[39m\n'"
    sample_without_ansi = "Some epsilon [default: 0.1]\n'"
    assert remove_ansii_escape_sequences(sample_with_ansii) == sample_without_ansi
