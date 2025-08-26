import pytest
from src.insight_synthesizer.cli import parse_file_selection


def test_parse_file_selection_all():
    assert parse_file_selection('all', 3) == {1, 2, 3}


def test_parse_file_selection_range():
    assert parse_file_selection('1-3', 3) == {1, 2, 3}


def test_parse_file_selection_list():
    assert parse_file_selection('1,3', 3) == {1, 3}


def test_parse_file_selection_invalid():
    with pytest.raises(ValueError):
        parse_file_selection('0', 3)
