"""Placeholder test to verify pytest discovers the test suite."""


def test_import():
    from src.resolve import __version__
    assert __version__ == "0.1.0"
