# Purpose: search_query.py parses Gmail-style search queries into a small expression tree
#
# Supported syntax:
#   mars rover          both words must match (AND is the default)
#   mars OR venus       either word matches (OR must be uppercase, like Gmail)
#   -mars               the word must NOT match
#   "south pole"        an exact phrase
#   tag:moon            missions tagged "moon" (tag:"ocean worlds" for multi-word tags)
#   (mars OR venus) radar   parentheses group terms
#
# Like Gmail, OR binds tighter than the implicit AND: "a OR b c" means "(a OR b) AND c"

import re
from dataclasses import dataclass

# limits that keep a single query from building a huge SQL statement
MAX_QUERY_LENGTH = 300
MAX_TERMS = 20
MAX_DEPTH = 5

# tag names: letters, digits, spaces, and hyphens, up to 30 characters
TAG_MAX_LENGTH = 30
TAG_PATTERN = re.compile(r"^[a-z0-9]+(?:[ -][a-z0-9]+)*$")


class QueryError(ValueError):
    """Raised when a search query can't be parsed"""


# ===== expression tree nodes ===== #
@dataclass(frozen=True)
class Text:
    value: str


@dataclass(frozen=True)
class Tag:
    name: str


@dataclass(frozen=True)
class Not:
    child: "Node"


@dataclass(frozen=True)
class And:
    children: tuple["Node", ...]


@dataclass(frozen=True)
class Or:
    children: tuple["Node", ...]


Node = Text | Tag | Not | And | Or


# function that normalizes a tag name: trims it, collapses spaces, and lowercases it
def normalize_tag(name: str) -> str:
    """
    Normalizes a tag name so "Mars", " mars " and "MARS" are the same tag

    Raises:
        QueryError: if the name is empty, too long, or has unsupported characters
    """
    normalized = " ".join(name.split()).lower()
    if not normalized:
        raise QueryError("Tag names can't be empty.")
    if len(normalized) > TAG_MAX_LENGTH:
        raise QueryError(f"Tag names can be at most {TAG_MAX_LENGTH} characters.")
    if not TAG_PATTERN.match(normalized):
        raise QueryError("Tag names can only use letters, digits, spaces, and hyphens.")
    return normalized


# a token is (kind, value), where kind is one of: "(", ")", "OR", "AND", "NOT", "TEXT", "TAG"
TOKEN_PATTERN = re.compile(
    r"""
    \s*(?:
        (?P<paren>[()])
      | (?P<neg>-)(?=\S)
      | (?P<tag>tag:(?:"[^"]*"?|[^\s()]*))
      | (?P<phrase>"[^"]*"?)
      | (?P<word>[^\s()"]+)
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)


def _unquote(value: str) -> str:
    if value.startswith('"'):
        value = value[1:]
        if value.endswith('"'):
            value = value[:-1]
    return value


def _tokenize(query: str) -> list[tuple[str, str]]:
    tokens: list[tuple[str, str]] = []
    position = 0
    while position < len(query):
        if query[position:].strip() == "":
            break
        match = TOKEN_PATTERN.match(query, position)
        if match is None or match.end() == position:
            raise QueryError("The search query couldn't be read.")
        position = match.end()

        if match.group("paren"):
            tokens.append((match.group("paren"), match.group("paren")))
        elif match.group("neg"):
            tokens.append(("NOT", "-"))
        elif match.group("tag"):
            value = _unquote(match.group("tag")[4:])
            tokens.append(("TAG", normalize_tag(value)))
        elif match.group("phrase"):
            value = " ".join(_unquote(match.group("phrase")).split())
            if value:
                tokens.append(("TEXT", value))
        else:
            word = match.group("word")
            # only uppercase OR / AND are operators, as in Gmail; "or" is a normal word
            if word in ("OR", "AND"):
                tokens.append((word, word))
            else:
                tokens.append(("TEXT", word))
    return tokens


class _Parser:
    def __init__(self, tokens: list[tuple[str, str]]) -> None:
        self.tokens = tokens
        self.position = 0
        self.terms = 0

    def _peek(self) -> str | None:
        return self.tokens[self.position][0] if self.position < len(self.tokens) else None

    def _take(self) -> tuple[str, str]:
        token = self.tokens[self.position]
        self.position += 1
        return token

    # and_expr := or_expr ([AND] or_expr)*
    def and_expr(self, depth: int) -> Node:
        children = [self.or_expr(depth)]
        while self._peek() not in (None, ")"):
            if self._peek() == "AND":
                self._take()
            children.append(self.or_expr(depth))
        return children[0] if len(children) == 1 else And(tuple(children))

    # or_expr := unary (OR unary)*
    def or_expr(self, depth: int) -> Node:
        children = [self.unary(depth)]
        while self._peek() == "OR":
            self._take()
            children.append(self.unary(depth))
        return children[0] if len(children) == 1 else Or(tuple(children))

    # unary := "-" unary | primary
    def unary(self, depth: int) -> Node:
        if self._peek() == "NOT":
            self._take()
            return Not(self.unary(depth))
        return self.primary(depth)

    # primary := "(" and_expr ")" | TAG | TEXT
    def primary(self, depth: int) -> Node:
        kind = self._peek()
        if kind is None:
            raise QueryError("The search query ends too early.")
        if kind == "(":
            if depth >= MAX_DEPTH:
                raise QueryError(f"Parentheses can be nested at most {MAX_DEPTH} levels deep.")
            self._take()
            if self._peek() == ")":
                raise QueryError("Parentheses can't be empty.")
            node = self.and_expr(depth + 1)
            if self._peek() != ")":
                raise QueryError("A parenthesis is missing a closing ')'.")
            self._take()
            return node
        if kind in ("TAG", "TEXT"):
            self.terms += 1
            if self.terms > MAX_TERMS:
                raise QueryError(f"A search can use at most {MAX_TERMS} terms.")
            _, value = self._take()
            return Tag(value) if kind == "TAG" else Text(value)
        if kind == ")":
            raise QueryError("A ')' has no matching '('.")
        raise QueryError(f"'{kind}' needs a search term on both sides.")


# function that parses a search query into an expression tree (or None for an empty query)
def parse_query(query: str) -> Node | None:
    """
    Parses a Gmail-style search query

    Returns:
        The expression tree, or None if the query is empty

    Raises:
        QueryError: if the query is malformed
    """
    query = query.strip()
    if len(query) > MAX_QUERY_LENGTH:
        raise QueryError(f"Search queries can be at most {MAX_QUERY_LENGTH} characters.")

    tokens = _tokenize(query)
    if not tokens:
        return None

    parser = _Parser(tokens)
    node = parser.and_expr(0)
    if parser.position != len(tokens):
        raise QueryError("A ')' has no matching '('.")
    return node
