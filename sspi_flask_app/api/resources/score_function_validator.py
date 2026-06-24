"""
Score Function Validator for Custom SSPI Configurations

This module provides secure validation and execution of user-provided score functions.
Score functions are strings that compute indicator scores from dataset values.

Security Model (whitelist-by-construction):
- A formal grammar + recursive-descent parser accepts ONLY well-formed score
  expressions and builds an AST. Anything off-grammar is rejected structurally,
  because there is simply no production for it (no `**`, `[]`, `.attr`, strings,
  comprehensions, statements, ...).
- ASCII-only input (homoglyph / fullwidth / zero-width / RTL defense).
- The AST is evaluated by a bounded AST walk — there is NO `exec`/`compile`, and no
  Python builtins are reachable from a score function.
- Maximum length enforcement (250 chars) caps resource-exhaustion inputs.
- `pow` exponents are bounded numeric literals; the top-level expression must be a
  goalpost (or aggregator of goalposts) so the output is provably in [0, 1].

See `.claude/plans/score-function-parser-design.md` for the grammar/AST design.

Valid Score Function Examples:
    "Score = goalpost(UNSDG_MARINE, 0, 100)"
    "Score = average(goalpost(X, 0, 1), goalpost(Y, 0, 1))"
    "Score = goalpost(A / B * 100, -10, 50)"
"""

import re
import math
import logging
from dataclasses import dataclass, field
from enum import Enum, auto

from sspi_flask_app.api.resources.utilities import goalpost

logger = logging.getLogger(__name__)


# =============================================================================
# Constants and Configuration
# =============================================================================

MAX_SCORE_FUNCTION_LENGTH = 250
MAX_EXPONENT_VALUE = 10  # Limit for pow() exponent to prevent DoS

# Allowed function names that can be called in score functions.
# NOTE: exp() intentionally excluded - too easy to cause overflow with dataset values
ALLOWED_FUNCTIONS = frozenset({
    "goalpost",
    "average",
    "max",
    "min",
    "abs",
    "sqrt",
    "pow",
    "log",
})

# Operators and punctuation allowed in score functions.
# NOTE: ** is NOT a production in the grammar - use pow() for safe exponentiation.
ALLOWED_OPERATORS = frozenset({
    "+", "-", "*", "/",         # Arithmetic (use pow() for exponentiation)
    "(", ")",                   # Grouping
    ",",                        # Function argument separator
    "=",                        # Assignment
})

# Special keywords/variables allowed
ALLOWED_KEYWORDS = frozenset({
    "Score",           # Assignment target
    "LowerGoalpost",   # Can be used as variable in some functions
    "UpperGoalpost",   # Can be used as variable in some functions
})

# Pattern for valid dataset codes (uppercase, starts with letter, 3-50 chars)
# Some dataset codes can be quite long (e.g., WID_NINCSH_POSTTAX_EQUALSPLIT_P0P50)
DATASET_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{2,49}$")

# Pattern for numbers (integers and floats, optionally negative)
NUMBER_PATTERN = re.compile(r"^-?\d+\.?\d*$")

# Functions that preserve [0, 1] bounds when given [0, 1] inputs.
# Used by the bounded-output proof.
BOUNDED_AGGREGATORS = frozenset(["average", "min", "max"])


# =============================================================================
# Token Types and Classes
# =============================================================================

class TokenType(Enum):
    """Types of tokens in a score function."""
    FUNCTION = auto()      # goalpost, average, max, etc.
    OPERATOR = auto()      # +, -, *, /, (, ), ,, =
    KEYWORD = auto()       # Score, LowerGoalpost, UpperGoalpost
    DATASET_CODE = auto()  # UNSDG_MARINE, WB_POPULN, etc.
    NUMBER = auto()        # 0, 100, -20, 0.5, 1.6
    WHITESPACE = auto()    # Spaces, newlines, tabs


@dataclass
class Token:
    """A single token from a score function."""
    type: TokenType
    value: str
    position: int  # Character position in original string


class ScoreFunctionValidationError(Exception):
    """Raised when score function validation fails."""

    def __init__(self, message: str, position: int | None = None):
        self.position = position
        if position is not None:
            message = f"{message} (at position {position})"
        super().__init__(message)


# =============================================================================
# AST Node Shapes
# =============================================================================
# The parser builds a small, closed set of AST nodes. Because these are the ONLY
# shapes the parser can produce, validation is whitelist-by-construction: there is
# no node for attribute access, indexing, strings, comprehensions, statements, etc.

@dataclass
class NumberLiteral:
    """A numeric literal, e.g. 0, 100, -20, 0.5."""
    value: float


@dataclass
class DatasetRef:
    """A reference to a dataset value, e.g. UNSDG_MARINE."""
    code: str


@dataclass
class GoalpostVar:
    """A reference to LowerGoalpost / UpperGoalpost as a variable."""
    name: str


@dataclass
class UnaryOp:
    """Unary negation, e.g. -factor."""
    operand: object
    op: str = "-"


@dataclass
class BinaryOp:
    """A binary arithmetic operation: op in {+, -, *, /}."""
    op: str
    left: object
    right: object


@dataclass
class FunctionCall:
    """A call to an allowed function, e.g. goalpost(X, 0, 1)."""
    name: str
    args: list


@dataclass
class Assignment:
    """The top-level `Score = <expression>` assignment."""
    expr: object
    target: str = "Score"


@dataclass
class ValidatedScoreFunction:
    """A validated and parsed score function ready for execution."""
    raw: str                              # Original string
    normalized: str                       # Whitespace-normalized version
    tokens: list[Token] = field(default_factory=list)
    dataset_codes: set[str] = field(default_factory=set)
    uses_goalposts_as_vars: bool = False  # True if uses LowerGoalpost/UpperGoalpost
    ast: Assignment | None = None         # Parsed AST (walked by safe_eval)


# =============================================================================
# Function tables (arity + runtime dispatch)
# =============================================================================

def _average(*args) -> float:
    """Compute arithmetic mean of arguments."""
    if not args:
        raise ValueError("average() requires at least one argument")
    return sum(args) / len(args)


def _safe_pow(base, exponent):
    """
    Bounded power function for safe exponentiation.

    The exponent is pre-validated at parse time (must be a numeric literal with
    abs(value) <= MAX_EXPONENT_VALUE), so runtime execution is safe. This is a
    thin wrapper around the ** operator.
    """
    return base ** exponent


# Fixed arity per function: (min_args, max_args); max_args = None means variadic.
FUNCTION_ARITY = {
    "goalpost": (3, 3),
    "pow": (2, 2),
    "sqrt": (1, 1),
    "abs": (1, 1),
    "log": (1, 1),
    "average": (1, None),
    "max": (1, None),
    "min": (1, None),
}

# Runtime dispatch map for the AST walk. No builtins beyond these are reachable.
FUNCTION_DISPATCH = {
    "goalpost": goalpost,
    "average": _average,
    "max": max,
    "min": min,
    "abs": abs,
    "sqrt": math.sqrt,
    "pow": _safe_pow,  # Bounded - exponent validated at parse time
    "log": math.log,
}


# =============================================================================
# Tokenizer
# =============================================================================

def tokenize_score_function(
    score_function: str,
    valid_dataset_codes: set[str] | None = None
) -> list[Token]:
    """
    Tokenize a score function string into typed tokens.

    The tokenizer is the first whitelist-by-construction layer: it accepts only
    ASCII input, the allowed single-character operators, numeric literals, and
    identifiers that are a known function, keyword, or valid-format/known dataset
    code. Everything else raises ScoreFunctionValidationError.

    Args:
        score_function: The score function string to tokenize
        valid_dataset_codes: Optional set of explicitly allowed dataset codes.
                            Identifiers in this set are accepted even if they
                            don't match the standard DATASET_CODE_PATTERN.

    Returns:
        List of Token objects

    Raises:
        ScoreFunctionValidationError: If an invalid character/token is found
    """
    # ASCII-only guard (homoglyph / fullwidth / zero-width / RTL defense).
    # This is a constructive whitelist ("input must be ASCII"), not a blacklist.
    for idx, char in enumerate(score_function):
        if ord(char) > 127:
            raise ScoreFunctionValidationError(
                f"Non-ASCII character not allowed: '{char}' (U+{ord(char):04X})", idx
            )

    tokens = []
    i = 0
    n = len(score_function)

    while i < n:
        char = score_function[i]

        # Whitespace - skip but track
        if char in " \t\n\r":
            while i < n and score_function[i] in " \t\n\r":
                i += 1
            # Don't add whitespace tokens - we'll normalize later
            continue

        # Single-character operators. There are no multi-char operators in the
        # grammar; sequences like ** / // / == become two operator tokens and are
        # rejected by the parser (no production accepts them).
        if char in "+-*/(),=":
            tokens.append(Token(TokenType.OPERATOR, char, i))
            i += 1
            continue

        # Numbers (including negative when in value context)
        # A negative sign is part of a number only if:
        # - Previous token is (, ,, =, or an operator (+, -, *, /)
        # - And followed by a digit
        is_negative_number = False
        if char == "-" and i + 1 < n and score_function[i + 1].isdigit():
            # Check if we're in a value context
            if not tokens:
                is_negative_number = True
            elif tokens[-1].type == TokenType.OPERATOR and tokens[-1].value in ("(", ",", "=", "+", "-", "*", "/"):
                is_negative_number = True

        if char.isdigit() or is_negative_number:
            start = i
            # Handle negative sign
            if char == "-":
                i += 1
            # Integer part
            while i < n and score_function[i].isdigit():
                i += 1
            # Decimal part
            if i < n and score_function[i] == ".":
                i += 1
                while i < n and score_function[i].isdigit():
                    i += 1
            value = score_function[start:i]
            tokens.append(Token(TokenType.NUMBER, value, start))
            continue

        # Identifiers (functions, keywords, dataset codes)
        if char.isalpha() or char == "_":
            start = i
            while i < n and (score_function[i].isalnum() or score_function[i] == "_"):
                i += 1
            value = score_function[start:i]

            # Determine token type
            if value in ALLOWED_FUNCTIONS:
                tokens.append(Token(TokenType.FUNCTION, value, start))
            elif value in ALLOWED_KEYWORDS:
                tokens.append(Token(TokenType.KEYWORD, value, start))
            elif DATASET_CODE_PATTERN.match(value):
                tokens.append(Token(TokenType.DATASET_CODE, value, start))
            # Accept explicitly provided dataset codes (even if short like "X")
            elif valid_dataset_codes is not None and value in valid_dataset_codes:
                tokens.append(Token(TokenType.DATASET_CODE, value, start))
            else:
                raise ScoreFunctionValidationError(
                    f"Unknown identifier '{value}'. Must be a known function, keyword, or valid dataset code",
                    start
                )
            continue

        # Unknown character (constructive reject: not whitespace/operator/digit/identifier)
        raise ScoreFunctionValidationError(
            f"Invalid character '{char}'",
            i
        )

    return tokens


# =============================================================================
# Recursive-descent Parser (token stream -> AST)
# =============================================================================
#
# Grammar (see design doc):
#   assignment    ::= "Score" "=" expression EOF
#   expression    ::= term (("+" | "-") term)*
#   term          ::= factor (("*" | "/") factor)*
#   factor        ::= NUMBER | dataset_ref | goalpost_var | function_call
#                   | "(" expression ")" | "-" factor
#   function_call ::= FUNCTION "(" expression ("," expression)* ")"

class _Parser:
    """Recursive-descent parser producing an Assignment AST root."""

    def __init__(self, tokens: list[Token]):
        self.tokens = tokens
        self.pos = 0

    def _peek(self) -> Token | None:
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None

    def _advance(self) -> Token:
        token = self.tokens[self.pos]
        self.pos += 1
        return token

    def _at_end(self) -> bool:
        return self.pos >= len(self.tokens)

    def _is_op(self, token: Token | None, value: str) -> bool:
        return token is not None and token.type == TokenType.OPERATOR and token.value == value

    # -- productions --------------------------------------------------------

    def parse(self) -> Assignment:
        if self._at_end():
            raise ScoreFunctionValidationError("Empty score function")

        head = self._peek()
        if not (head.type == TokenType.KEYWORD and head.value == "Score"):
            raise ScoreFunctionValidationError(
                "Score function must start with 'Score'", head.position
            )
        self._advance()

        eq = self._peek()
        if not self._is_op(eq, "="):
            pos = eq.position if eq is not None else head.position
            raise ScoreFunctionValidationError("Expected '=' after 'Score'", pos)
        self._advance()

        if self._at_end():
            raise ScoreFunctionValidationError("Score function must assign an expression to 'Score'")

        expr = self.parse_expression()

        if not self._at_end():
            extra = self._peek()
            if self._is_op(extra, ")"):
                raise ScoreFunctionValidationError("Unbalanced parenthesis: unmatched ')'", extra.position)
            raise ScoreFunctionValidationError(
                f"Unexpected trailing token '{extra.value}' after expression", extra.position
            )

        return Assignment(expr=expr)

    def parse_expression(self):
        node = self.parse_term()
        while True:
            token = self._peek()
            if token is not None and token.type == TokenType.OPERATOR and token.value in ("+", "-"):
                op = self._advance().value
                right = self.parse_term()
                node = BinaryOp(op, node, right)
            else:
                break
        return node

    def parse_term(self):
        node = self.parse_factor()
        while True:
            token = self._peek()
            if token is not None and token.type == TokenType.OPERATOR and token.value in ("*", "/"):
                op = self._advance().value
                right = self.parse_factor()
                node = BinaryOp(op, node, right)
            else:
                break
        return node

    def parse_factor(self):
        token = self._peek()
        if token is None:
            raise ScoreFunctionValidationError("Unexpected end of expression")

        # Unary minus
        if self._is_op(token, "-"):
            self._advance()
            return UnaryOp(self.parse_factor())

        if token.type == TokenType.NUMBER:
            self._advance()
            return NumberLiteral(self._number_value(token))

        if token.type == TokenType.DATASET_CODE:
            self._advance()
            return DatasetRef(token.value)

        if token.type == TokenType.KEYWORD and token.value in ("LowerGoalpost", "UpperGoalpost"):
            self._advance()
            return GoalpostVar(token.value)

        if token.type == TokenType.FUNCTION:
            return self.parse_function_call()

        if self._is_op(token, "("):
            self._advance()
            node = self.parse_expression()
            close = self._peek()
            if not self._is_op(close, ")"):
                pos = close.position if close is not None else token.position
                raise ScoreFunctionValidationError("Unbalanced parenthesis: expected ')'", pos)
            self._advance()
            return node

        raise ScoreFunctionValidationError(
            f"Unexpected token '{token.value}' in expression", token.position
        )

    def parse_function_call(self):
        func = self._advance()  # FUNCTION token
        name = func.value

        paren = self._peek()
        if not self._is_op(paren, "("):
            pos = paren.position if paren is not None else func.position
            raise ScoreFunctionValidationError(f"Expected '(' after function '{name}'", pos)
        self._advance()  # consume '('

        # No allowed function is nullary; an empty arg list is a parse error.
        nxt = self._peek()
        if self._is_op(nxt, ")"):
            raise ScoreFunctionValidationError(
                f"Function '{name}' requires at least one argument", nxt.position
            )

        args = [self.parse_expression()]
        while self._is_op(self._peek(), ","):
            self._advance()  # consume ','
            args.append(self.parse_expression())

        close = self._peek()
        if not self._is_op(close, ")"):
            pos = close.position if close is not None else func.position
            raise ScoreFunctionValidationError(
                f"Unbalanced parenthesis: expected ')' to close '{name}('", pos
            )
        self._advance()  # consume ')'

        self._check_arity(name, args, func.position)
        if name == "pow":
            self._check_pow(args, func.position)

        return FunctionCall(name, args)

    # -- per-reduction validation ------------------------------------------

    def _check_arity(self, name: str, args: list, position: int) -> None:
        min_args, max_args = FUNCTION_ARITY[name]
        count = len(args)
        if count < min_args or (max_args is not None and count > max_args):
            if max_args is None:
                expected = f"at least {min_args}"
            elif min_args == max_args:
                expected = f"exactly {min_args}"
            else:
                expected = f"between {min_args} and {max_args}"
            raise ScoreFunctionValidationError(
                f"Function '{name}' expects {expected} argument(s), got {count}", position
            )

    def _check_pow(self, args: list, position: int) -> None:
        # Arity (2) already enforced by _check_arity.
        exponent = _constant_value(args[1])
        if exponent is None:
            raise ScoreFunctionValidationError(
                "pow() exponent must be a numeric literal, not a dataset code or expression. "
                "Dataset exponentiation cannot be pre-validated for safety.",
                position,
            )
        if abs(exponent) > MAX_EXPONENT_VALUE:
            raise ScoreFunctionValidationError(
                f"pow() exponent {exponent} exceeds maximum allowed ({MAX_EXPONENT_VALUE})",
                position,
            )

    @staticmethod
    def _number_value(token: Token) -> float:
        try:
            return float(token.value)
        except ValueError:
            raise ScoreFunctionValidationError(
                f"Invalid number '{token.value}'", token.position
            )


def _constant_value(node) -> float | None:
    """Return the constant float value of a literal node, or None if not constant."""
    if isinstance(node, NumberLiteral):
        return node.value
    if isinstance(node, UnaryOp) and node.op == "-":
        inner = _constant_value(node.operand)
        return None if inner is None else -inner
    return None


# =============================================================================
# Post-parse AST predicates
# =============================================================================

def _is_bounded(node) -> bool:
    """
    True iff `node` is provably in [0, 1].

    A node is bounded iff it is goalpost(...) (always maps into [0, 1]) or an
    aggregator in BOUNDED_AGGREGATORS (average/min/max) all of whose arguments are
    bounded. Raw datasets, bare numbers, sums/products, and non-bounding functions
    (pow/sqrt/log/abs) are NOT bounded.
    """
    if isinstance(node, FunctionCall):
        if node.name == "goalpost":
            return True
        if node.name in BOUNDED_AGGREGATORS:
            return all(_is_bounded(arg) for arg in node.args)
    return False


def _collect_refs(node, dataset_codes: set[str], flags: dict) -> None:
    """Walk the AST collecting dataset codes and goalpost-variable usage."""
    if isinstance(node, DatasetRef):
        dataset_codes.add(node.code)
    elif isinstance(node, GoalpostVar):
        flags["uses_goalposts_as_vars"] = True
    elif isinstance(node, UnaryOp):
        _collect_refs(node.operand, dataset_codes, flags)
    elif isinstance(node, BinaryOp):
        _collect_refs(node.left, dataset_codes, flags)
        _collect_refs(node.right, dataset_codes, flags)
    elif isinstance(node, FunctionCall):
        for arg in node.args:
            _collect_refs(arg, dataset_codes, flags)
    elif isinstance(node, Assignment):
        _collect_refs(node.expr, dataset_codes, flags)
    # NumberLiteral: nothing to collect


# =============================================================================
# Public Validator
# =============================================================================

def validate_score_function(
    score_function: str,
    valid_dataset_codes: set[str] | None = None
) -> ValidatedScoreFunction:
    """
    Validate a score function string for safe execution.

    This is the main entry point for score function validation. It tokenizes the
    input, parses it into an AST (rejecting anything off-grammar), enforces arity /
    pow-exponent / bounded-output / dataset-existence rules, and returns a
    ValidatedScoreFunction carrying the AST for later evaluation by safe_eval.

    Args:
        score_function: Raw score function string (max 250 chars)
        valid_dataset_codes: Optional set of allowed dataset codes.
                            If None, any valid-format dataset code is allowed.

    Returns:
        ValidatedScoreFunction object ready for execution

    Raises:
        ScoreFunctionValidationError: If validation fails
    """
    # Length check (caps resource-exhaustion / deeply-nested inputs before parsing)
    if len(score_function) > MAX_SCORE_FUNCTION_LENGTH:
        raise ScoreFunctionValidationError(
            f"Score function exceeds maximum length of {MAX_SCORE_FUNCTION_LENGTH} characters "
            f"(got {len(score_function)})"
        )

    if not score_function or not score_function.strip():
        raise ScoreFunctionValidationError("Score function cannot be empty")

    # Tokenize (ASCII guard + character/identifier whitelist).
    tokens = tokenize_score_function(score_function, valid_dataset_codes)

    # Parse to an AST. The parser rejects anything off-grammar by construction and
    # enforces arity + pow-exponent rules during reduction.
    ast = _Parser(tokens).parse()

    # Bounded-[0, 1]-output proof on the parsed AST.
    if not _is_bounded(ast.expr):
        raise ScoreFunctionValidationError(
            "Score must be a goalpost() result, or an average/min/max of goalposted "
            "values, to guarantee output in [0, 1]"
        )

    # Collect dataset codes and goalpost-variable usage from the AST.
    dataset_codes: set[str] = set()
    flags = {"uses_goalposts_as_vars": False}
    _collect_refs(ast, dataset_codes, flags)

    # Dataset-code existence (strict when an allowed set is supplied).
    if valid_dataset_codes is not None:
        for code in dataset_codes:
            if code not in valid_dataset_codes:
                raise ScoreFunctionValidationError(f"Unknown dataset code '{code}'")

    normalized = normalize_score_function(tokens)

    return ValidatedScoreFunction(
        raw=score_function,
        normalized=normalized,
        tokens=tokens,
        dataset_codes=dataset_codes,
        uses_goalposts_as_vars=flags["uses_goalposts_as_vars"],
        ast=ast,
    )


def normalize_score_function(tokens: list[Token]) -> str:
    """
    Reconstruct a normalized score function string from tokens.

    Used to populate ValidatedScoreFunction.normalized for display / echo (e.g. the
    /validate response). It is no longer executed.
    """
    parts = []
    for token in tokens:
        if token.type == TokenType.OPERATOR:
            if token.value == ",":
                parts.append(", ")
            elif token.value == "=":
                parts.append(" = ")
            elif token.value in ("(", ")"):
                parts.append(token.value)
            else:
                # Binary operators get spaces
                parts.append(f" {token.value} ")
        else:
            parts.append(token.value)

    # Clean up extra spaces
    result = "".join(parts)
    result = re.sub(r" +", " ", result)
    result = re.sub(r"\( ", "(", result)
    result = re.sub(r" \)", ")", result)

    return result.strip()


# =============================================================================
# Safe Execution (bounded AST walk - NO exec)
# =============================================================================

def _eval(node, env: dict):
    """Evaluate an AST node against an environment of dataset/goalpost values."""
    if isinstance(node, Assignment):
        return _eval(node.expr, env)
    if isinstance(node, NumberLiteral):
        return node.value
    if isinstance(node, DatasetRef):
        return env[node.code]
    if isinstance(node, GoalpostVar):
        return env[node.name]
    if isinstance(node, UnaryOp):
        return -_eval(node.operand, env)
    if isinstance(node, BinaryOp):
        left = _eval(node.left, env)
        right = _eval(node.right, env)
        if node.op == "+":
            return left + right
        if node.op == "-":
            return left - right
        if node.op == "*":
            return left * right
        if node.op == "/":
            return left / right
        raise ScoreFunctionValidationError(f"Unknown operator '{node.op}'")
    if isinstance(node, FunctionCall):
        func = FUNCTION_DISPATCH[node.name]
        return func(*[_eval(arg, env) for arg in node.args])
    raise ScoreFunctionValidationError(f"Cannot evaluate node of type {type(node).__name__}")


def safe_eval(
    validated_function: ValidatedScoreFunction,
    dataset_values: dict[str, float],
    lower_goalpost: float | None = None,
    upper_goalpost: float | None = None,
) -> float:
    """
    Safely evaluate a validated score function with dataset values.

    Evaluation walks the AST built at validation time; there is no exec/compile and
    no Python builtins are reachable. The parse happens once (in
    validate_score_function); this is a cheap per-call walk suitable for the
    per-(country, year) hot loop in fast_custom_scoring.py.

    Args:
        validated_function: Pre-validated score function (carrying its AST)
        dataset_values: Dict mapping dataset codes to float values
        lower_goalpost: Optional value for LowerGoalpost variable
        upper_goalpost: Optional value for UpperGoalpost variable

    Returns:
        Computed score (typically 0-1 range, but not clamped here)

    Raises:
        ValueError: If required dataset values are missing
        ScoreFunctionValidationError: If execution fails or the result is non-finite
    """
    # Check all required dataset codes are present
    missing = validated_function.dataset_codes - set(dataset_values.keys())
    if missing:
        raise ValueError(f"Missing dataset values: {missing}")

    if validated_function.ast is None:
        raise ScoreFunctionValidationError("Score function has no parsed AST to evaluate")

    # Build evaluation environment
    env = dict(dataset_values)
    if validated_function.uses_goalposts_as_vars:
        if lower_goalpost is not None:
            env["LowerGoalpost"] = lower_goalpost
        if upper_goalpost is not None:
            env["UpperGoalpost"] = upper_goalpost

    try:
        score = _eval(validated_function.ast, env)
    except ScoreFunctionValidationError:
        raise
    except Exception as e:
        raise ScoreFunctionValidationError(
            f"Score function execution failed: {type(e).__name__}: {e}"
        )

    if score is None:
        raise ScoreFunctionValidationError(
            "Score function did not produce a value"
        )

    if not isinstance(score, (int, float)):
        raise ScoreFunctionValidationError(
            f"Score must be a number, got {type(score).__name__}"
        )

    if math.isnan(score) or math.isinf(score):
        raise ScoreFunctionValidationError(
            f"Score is not a finite number: {score}"
        )

    return float(score)


# =============================================================================
# Convenience Functions
# =============================================================================

def validate_and_execute(
    score_function: str,
    dataset_values: dict[str, float],
    valid_dataset_codes: set[str] | None = None,
    lower_goalpost: float | None = None,
    upper_goalpost: float | None = None,
) -> float:
    """
    Validate and execute a score function in one step.

    Convenience function that combines validation and execution.

    Args:
        score_function: Raw score function string
        dataset_values: Dict mapping dataset codes to float values
        valid_dataset_codes: Optional set of allowed dataset codes
        lower_goalpost: Optional value for LowerGoalpost variable
        upper_goalpost: Optional value for UpperGoalpost variable

    Returns:
        Computed score
    """
    validated = validate_score_function(score_function, valid_dataset_codes)
    return safe_eval(validated, dataset_values, lower_goalpost, upper_goalpost)
