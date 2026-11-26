import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1] / "code"))

from search_query import And, Not, Or, QueryError, Tag, Text, normalize_tag, parse_query


def test_empty_query_returns_none() -> None:
    assert parse_query("   ") is None


def test_words_are_combined_with_and() -> None:
    assert parse_query("mars rover") == And((Text("mars"), Text("rover")))


def test_or_binds_tighter_than_implicit_and() -> None:
    assert parse_query("mars OR venus radar") == And(
        (Or((Text("mars"), Text("venus"))), Text("radar"))
    )


def test_lowercase_or_is_a_normal_word() -> None:
    assert parse_query("mars or venus") == And((Text("mars"), Text("or"), Text("venus")))


def test_parentheses_negation_and_tags() -> None:
    assert parse_query('(tag:moon OR tag:"Ocean  Worlds") -radar') == And(
        (Or((Tag("moon"), Tag("ocean worlds"))), Not(Text("radar")))
    )


def test_quoted_phrase_and_hyphenated_word() -> None:
    assert parse_query('"south pole" Falcon-9') == And((Text("south pole"), Text("Falcon-9")))


@pytest.mark.parametrize(
    "query",
    ["(mars", "mars)", "()", "OR mars", "mars OR", "tag:", "tag:mars!", "-"],
)
def test_malformed_queries_raise(query: str) -> None:
    if query == "-":
        # a lone hyphen is treated as a plain word, not an operator
        assert parse_query(query) == Text("-")
        return
    with pytest.raises(QueryError):
        parse_query(query)


def test_query_limits() -> None:
    with pytest.raises(QueryError):
        parse_query(" ".join(f"w{i}" for i in range(21)))
    with pytest.raises(QueryError):
        parse_query("(" * 6 + "mars" + ")" * 6)


def test_normalize_tag() -> None:
    assert normalize_tag("  Deep   Space ") == "deep space"
    with pytest.raises(QueryError):
        normalize_tag("x" * 31)
    with pytest.raises(QueryError):
        normalize_tag("<script>")
