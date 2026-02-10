"""
Score Function Validator for Custom SSPI Configurations

This module provides secure validation and execution of user-provided score functions.
Score functions are strings that compute indicator scores from dataset values.

Security Model:
- Strict token whitelist (no arbitrary code execution)
- No Python builtins in execution context
- Maximum length enforcement (250 chars)
- Pre-validation before any execution

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
from typing import Callable

from sspi_flask_app.api.resources.utilities import goalpost

logger = logging.getLogger(__name__)


# =============================================================================
# Constants and Configuration
# =============================================================================

MAX_SCORE_FUNCTION_LENGTH = 250
MAX_EXPONENT_VALUE = 10  # Limit for pow() exponent to prevent DoS

# Whitelist of allowed ASCII characters in score functions
# Defense in depth: blocks unicode homoglyphs and unexpected characters
ALLOWED_CHARACTERS = frozenset(
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    "_"           # Underscores in identifiers
    " \t\n\r"     # Whitespace
    "+-*/()"      # Operators (note: * is single, ** will be blocked by pattern)
    ",."          # Comma and decimal point
    "="           # Assignment
)

# Allowed function names that can be called in score functions
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

# Operators and punctuation allowed in score functions
# NOTE: ** is NOT allowed - use pow() function instead for safe exponentiation
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

# Dangerous patterns that should NEVER appear (case-insensitive check)
DANGEROUS_PATTERNS = [
    r"\*\*",            # Exponentiation operator - use pow() instead
    r"\^",              # Bitwise XOR (often confused with exponentiation)
    r"==",              # Comparison operator (not assignment)
    r"__",              # Dunder methods
    r"\bimport\b",      # Import statements
    r"\bexec\b",        # Exec function
    r"\beval\b",        # Eval function
    r"\bcompile\b",     # Compile function
    r"\bopen\b",        # File operations
    r"\bfile\b",        # File operations
    r"\bgetattr\b",     # Attribute access
    r"\bsetattr\b",     # Attribute setting
    r"\bdelattr\b",     # Attribute deletion
    r"\bglobals\b",     # Global access
    r"\blocals\b",      # Local access
    r"\bvars\b",        # Variable access
    r"\bdir\b",         # Directory listing
    r"\blambda\b",      # Lambda expressions
    r"\bclass\b",       # Class definitions
    r"\bdef\b",         # Function definitions
    r"\bfor\b",         # For loops
    r"\bwhile\b",       # While loops
    r"\bif\b",          # Conditionals (outside ternary)
    r"\belse\b",        # Conditionals
    r"\btry\b",         # Exception handling
    r"\bexcept\b",      # Exception handling
    r"\braise\b",       # Exception raising
    r"\bwith\b",        # Context managers
    r"\bassert\b",      # Assertions
    r"\byield\b",       # Generators
    r"\basync\b",       # Async
    r"\bawait\b",       # Await
    r"['\"]",           # String literals
    r"\[",              # List comprehensions/indexing
    r"\]",              # List comprehensions/indexing
    r"\{",              # Dict comprehensions/sets
    r"\}",              # Dict comprehensions/sets
    r";",               # Statement separator
    r"\\",              # Escape sequences
]

# Pattern for valid dataset codes (uppercase, starts with letter, 3-50 chars)
# Some dataset codes can be quite long (e.g., WID_NINCSH_POSTTAX_EQUALSPLIT_P0P50)
DATASET_CODE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{2,49}$")

# Pattern for numbers (integers and floats, optionally negative)
NUMBER_PATTERN = re.compile(r"^-?\d+\.?\d*$")

# Functions that preserve [0, 1] bounds when given [0, 1] inputs
# Used for validate_bounded_output()
BOUNDED_AGGREGATORS = frozenset(["average", "min", "max"])


# =============================================================================
# Token Types and Classes
# =============================================================================

class TokenType(Enum):
    """Types of tokens in a score function."""
    FUNCTION = auto()      # goalpost, average, max, etc.
    OPERATOR = auto()      # +, -, *, /, **, (, ), ,, =
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


@dataclass
class ValidatedScoreFunction:
    """A validated and parsed score function ready for execution."""
    raw: str                              # Original string
    normalized: str                       # Whitespace-normalized version
    tokens: list[Token] = field(default_factory=list)
    dataset_codes: set[str] = field(default_factory=set)
    uses_goalposts_as_vars: bool = False  # True if uses LowerGoalpost/UpperGoalpost


class ScoreFunctionValidationError(Exception):
    """Raised when score function validation fails."""

    def __init__(self, message: str, position: int | None = None):
        self.position = position
        if position is not None:
            message = f"{message} (at position {position})"
        super().__init__(message)


# =============================================================================
# Pre-Validation
# =============================================================================

def pre_validate_characters(score_function: str) -> str:
    """
    Pre-validate a score function string before tokenization.

    Performs conservative whitelist-based validation:
    1. Rejects any non-ASCII characters (prevents unicode homoglyph attacks)
    2. Normalizes whitespace
    3. Ensures string begins with 'Score' followed by '='
    4. Ensures only whitelisted characters are present

    Args:
        score_function: Raw score function string

    Returns:
        Whitespace-normalized score function string

    Raises:
        ScoreFunctionValidationError: If pre-validation fails
    """
    # Step 1: ASCII only - reject any non-ASCII characters
    for i, char in enumerate(score_function):
        if ord(char) > 127:
            raise ScoreFunctionValidationError(
                f"Non-ASCII character not allowed: '{char}' (U+{ord(char):04X})", i
            )

    # Step 2: Normalize whitespace
    normalized = ' '.join(score_function.split())

    # Step 3: Check it starts with "Score"
    if not normalized.startswith("Score"):
        raise ScoreFunctionValidationError("Score function must start with 'Score'")

    # Step 4: Check that '=' follows 'Score' (with optional whitespace)
    rest = normalized[5:].lstrip()
    if not rest.startswith("="):
        raise ScoreFunctionValidationError("Score function must have '=' after 'Score'")

    # Step 5: Check only allowed characters
    for i, char in enumerate(score_function):
        if char not in ALLOWED_CHARACTERS:
            raise ScoreFunctionValidationError(
                f"Invalid character '{char}' (U+{ord(char):04X})", i
            )

    return normalized


# =============================================================================
# Safe Execution Context
# =============================================================================

def _average(*args) -> float:
    """Compute arithmetic mean of arguments."""
    if not args:
        raise ValueError("average() requires at least one argument")
    return sum(args) / len(args)


def _safe_pow(base, exponent):
    """
    Bounded power function for safe exponentiation.

    The exponent is pre-validated at parse time by validate_pow_arguments(),
    so runtime execution is safe. This function is just a thin wrapper.

    Args:
        base: The base value (can be a dataset value)
        exponent: The exponent (must be a numeric literal, validated at parse time)

    Returns:
        base raised to exponent power
    """
    return base ** exponent


# Safe global context for exec() - NO BUILTINS
# NOTE: exp() intentionally excluded - too easy to cause overflow
SAFE_GLOBALS = {
    "__builtins__": {},  # Critical: disable all builtins
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

        # Single-character operators (** is banned, caught by dangerous patterns)
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

        # Unknown character
        raise ScoreFunctionValidationError(
            f"Invalid character '{char}'",
            i
        )

    return tokens


# =============================================================================
# Validator
# =============================================================================

def check_dangerous_patterns(score_function: str) -> None:
    """
    Check for dangerous patterns that should never appear in score functions.

    Args:
        score_function: The raw score function string

    Raises:
        ScoreFunctionValidationError: If a dangerous pattern is found
    """
    for pattern in DANGEROUS_PATTERNS:
        match = re.search(pattern, score_function, re.IGNORECASE)
        if match:
            raise ScoreFunctionValidationError(
                f"Dangerous pattern detected: '{match.group()}'",
                match.start()
            )


def validate_pow_arguments(tokens: list[Token]) -> None:
    """
    Validate that pow() function calls have safe arguments.

    Ensures:
    - pow() exponent (second argument) is a numeric literal, not a dataset code
    - Exponent value does not exceed MAX_EXPONENT_VALUE

    This prevents:
    - pow(DATASET_A, DATASET_B) - can't prevalidate dataset exponent
    - pow(10, DATASET_A) - can't prevalidate dataset exponent
    - pow(10, 100) - exponent too large

    Allows:
    - pow(DATASET_A, 2) - dataset to literal power
    - pow(10, 8) - literal to literal power

    Args:
        tokens: List of tokens from the score function

    Raises:
        ScoreFunctionValidationError: If pow() has invalid arguments
    """
    for i, token in enumerate(tokens):
        if token.type == TokenType.FUNCTION and token.value == "pow":
            if i + 1 >= len(tokens) or tokens[i + 1].value != "(":
                continue

            # Find the comma separating base from exponent
            paren_depth = 1
            j = i + 2
            while j < len(tokens) and paren_depth > 0:
                if tokens[j].value == "(":
                    paren_depth += 1
                elif tokens[j].value == ")":
                    paren_depth -= 1
                elif tokens[j].value == "," and paren_depth == 1:
                    # Found the comma - check the exponent (next token)
                    if j + 1 < len(tokens):
                        exp_token = tokens[j + 1]
                        if exp_token.type == TokenType.DATASET_CODE:
                            raise ScoreFunctionValidationError(
                                f"pow() exponent must be a numeric literal, not dataset code '{exp_token.value}'. "
                                "Dataset exponentiation cannot be pre-validated for safety.",
                                exp_token.position
                            )
                        elif exp_token.type == TokenType.NUMBER:
                            # Validate the exponent value
                            try:
                                exp_val = abs(float(exp_token.value))
                                if exp_val > MAX_EXPONENT_VALUE:
                                    raise ScoreFunctionValidationError(
                                        f"pow() exponent {exp_token.value} exceeds maximum allowed ({MAX_EXPONENT_VALUE})",
                                        exp_token.position
                                    )
                            except ValueError:
                                pass
                    break
                j += 1


def validate_bounded_output(tokens: list[Token]) -> None:
    """
    Validate that the Score expression is guaranteed to return [0, 1].

    The expression after 'Score =' must be:
    - goalpost(...) - always returns [0, 1]
    - OR average/min/max of bounded expressions (recursively)

    Invalid patterns that could escape [0, 1]:
    - Score = DATASET_A (raw dataset value)
    - Score = goalpost(...) + goalpost(...) (sum could exceed 1)
    - Score = goalpost(...) * 2 (multiplication could exceed 1)
    - Score = 0.5 (raw number)

    Args:
        tokens: List of tokens from the score function

    Raises:
        ScoreFunctionValidationError: If unbounded path exists
    """
    # tokens[0] = 'Score', tokens[1] = '=', tokens[2:] = expression
    if len(tokens) < 3:
        raise ScoreFunctionValidationError("Expression too short")

    # Validate the expression starting at index 2
    _validate_bounded_expr(tokens, 2)


def _validate_bounded_expr(tokens: list[Token], start: int) -> int:
    """
    Recursively validate that expression starting at tokens[start] is bounded.

    A bounded expression must be:
    1. goalpost(...) - always bounded
    2. average/min/max of bounded expressions

    Args:
        tokens: Full token list
        start: Starting index in tokens

    Returns:
        Index after the end of this expression

    Raises:
        ScoreFunctionValidationError: If expression is not bounded
    """
    if start >= len(tokens):
        raise ScoreFunctionValidationError("Empty expression")

    first = tokens[start]

    # Must start with a function
    if first.type != TokenType.FUNCTION:
        raise ScoreFunctionValidationError(
            f"Score must be result of goalpost() or average/min/max of goalposted values. "
            f"Found '{first.value}' instead of a bounding function.",
            first.position
        )

    func_name = first.value

    if func_name == "goalpost":
        # goalpost() is always bounded - skip to end of function call
        return _skip_function_call(tokens, start)

    if func_name in BOUNDED_AGGREGATORS:
        # average/min/max - must validate each argument is bounded
        return _validate_aggregator_arguments(tokens, start)

    # Other functions (pow, sqrt, log, exp, abs) at top level are NOT bounded
    raise ScoreFunctionValidationError(
        f"Score must be result of goalpost() or average/min/max of goalposted values. "
        f"Function '{func_name}' does not guarantee [0, 1] output.",
        first.position
    )


def _skip_function_call(tokens: list[Token], func_start: int) -> int:
    """
    Skip over a function call, returning the index after the closing paren.

    Args:
        tokens: Full token list
        func_start: Index of the function name token

    Returns:
        Index after the closing parenthesis
    """
    if func_start + 1 >= len(tokens) or tokens[func_start + 1].value != "(":
        return func_start + 1

    paren_depth = 0
    i = func_start + 1
    while i < len(tokens):
        if tokens[i].value == "(":
            paren_depth += 1
        elif tokens[i].value == ")":
            paren_depth -= 1
            if paren_depth == 0:
                return i + 1
        i += 1
    return i


def _validate_aggregator_arguments(tokens: list[Token], func_start: int) -> int:
    """
    Validate that all arguments to an aggregator function are bounded.

    Args:
        tokens: Full token list
        func_start: Index of the aggregator function name token

    Returns:
        Index after the closing parenthesis

    Raises:
        ScoreFunctionValidationError: If any argument is not bounded
    """
    if func_start + 1 >= len(tokens) or tokens[func_start + 1].value != "(":
        raise ScoreFunctionValidationError(
            f"Expected '(' after {tokens[func_start].value}",
            func_start
        )

    paren_depth = 1
    i = func_start + 2  # Start after '('

    while i < len(tokens) and paren_depth > 0:
        tok = tokens[i]

        if tok.value == "(":
            paren_depth += 1
            i += 1
        elif tok.value == ")":
            paren_depth -= 1
            if paren_depth == 0:
                return i + 1
            i += 1
        elif tok.value == "," and paren_depth == 1:
            # Skip the comma
            i += 1
        elif tok.type == TokenType.FUNCTION:
            # Validate this argument as a bounded expression
            i = _validate_bounded_expr(tokens, i)
        else:
            # Non-function token at argument start is invalid
            raise ScoreFunctionValidationError(
                f"Expected bounded expression (goalpost or average/min/max), "
                f"found '{tok.value}'",
                tok.position
            )

    return i


def validate_token_sequence(tokens: list[Token]) -> None:
    """
    Validate the sequence of tokens for basic syntactic correctness.

    Args:
        tokens: List of tokens to validate

    Raises:
        ScoreFunctionValidationError: If token sequence is invalid
    """
    if not tokens:
        raise ScoreFunctionValidationError("Empty score function")

    # Must start with "Score ="
    if len(tokens) < 3:
        raise ScoreFunctionValidationError(
            "Score function must be at least 'Score = <expression>'"
        )

    if tokens[0].type != TokenType.KEYWORD or tokens[0].value != "Score":
        raise ScoreFunctionValidationError(
            "Score function must start with 'Score'",
            tokens[0].position
        )

    if tokens[1].type != TokenType.OPERATOR or tokens[1].value != "=":
        raise ScoreFunctionValidationError(
            "Expected '=' after 'Score'",
            tokens[1].position
        )

    # Check balanced parentheses
    paren_depth = 0
    for token in tokens:
        if token.type == TokenType.OPERATOR:
            if token.value == "(":
                paren_depth += 1
            elif token.value == ")":
                paren_depth -= 1
                if paren_depth < 0:
                    raise ScoreFunctionValidationError(
                        "Unmatched closing parenthesis",
                        token.position
                    )

    if paren_depth != 0:
        raise ScoreFunctionValidationError(
            f"Unmatched opening parenthesis ({paren_depth} unclosed)"
        )


def validate_score_function(
    score_function: str,
    valid_dataset_codes: set[str] | None = None
) -> ValidatedScoreFunction:
    """
    Validate a score function string for safe execution.

    This is the main entry point for score function validation.

    Args:
        score_function: Raw score function string (max 250 chars)
        valid_dataset_codes: Optional set of allowed dataset codes.
                            If None, any valid-format dataset code is allowed.

    Returns:
        ValidatedScoreFunction object ready for execution

    Raises:
        ScoreFunctionValidationError: If validation fails
    """
    # Length check
    if len(score_function) > MAX_SCORE_FUNCTION_LENGTH:
        raise ScoreFunctionValidationError(
            f"Score function exceeds maximum length of {MAX_SCORE_FUNCTION_LENGTH} characters "
            f"(got {len(score_function)})"
        )

    if not score_function or not score_function.strip():
        raise ScoreFunctionValidationError("Score function cannot be empty")
    # Pre-validate characters (ASCII only, whitelist, Score= prefix)
    pre_validate_characters(score_function)
    # Check for dangerous patterns before any parsing
    check_dangerous_patterns(score_function)
    # Tokenize (pass valid_dataset_codes to accept short codes like "X" if explicit)
    tokens = tokenize_score_function(score_function, valid_dataset_codes)
    # Validate pow() arguments (exponent must be numeric literal <= 10)
    validate_pow_arguments(tokens)
    # Validate token sequence
    validate_token_sequence(tokens)
    # Validate that output is guaranteed to be [0, 1]
    validate_bounded_output(tokens)
    # Collect dataset codes and validate against allowed list if provided
    dataset_codes = set()
    uses_goalposts_as_vars = False

    for token in tokens:
        if token.type == TokenType.DATASET_CODE:
            dataset_codes.add(token.value)
            if valid_dataset_codes is not None and token.value not in valid_dataset_codes:
                raise ScoreFunctionValidationError(
                    f"Unknown dataset code '{token.value}'",
                    token.position
                )
        elif token.type == TokenType.KEYWORD and token.value in ("LowerGoalpost", "UpperGoalpost"):
            uses_goalposts_as_vars = True

    # Normalize whitespace for execution
    normalized = normalize_score_function(tokens)

    return ValidatedScoreFunction(
        raw=score_function,
        normalized=normalized,
        tokens=tokens,
        dataset_codes=dataset_codes,
        uses_goalposts_as_vars=uses_goalposts_as_vars,
    )


def normalize_score_function(tokens: list[Token]) -> str:
    """
    Reconstruct a normalized score function string from tokens.

    Ensures consistent formatting for execution.
    """
    parts = []
    for i, token in enumerate(tokens):
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
# Safe Execution
# =============================================================================

def safe_eval(
    validated_function: ValidatedScoreFunction,
    dataset_values: dict[str, float],
    lower_goalpost: float | None = None,
    upper_goalpost: float | None = None,
) -> float:
    """
    Safely evaluate a validated score function with dataset values.

    Args:
        validated_function: Pre-validated score function
        dataset_values: Dict mapping dataset codes to float values
        lower_goalpost: Optional value for LowerGoalpost variable
        upper_goalpost: Optional value for UpperGoalpost variable

    Returns:
        Computed score (typically 0-1 range, but not clamped here)

    Raises:
        ValueError: If required dataset values are missing
        ScoreFunctionValidationError: If execution fails
    """
    # Check all required dataset codes are present
    missing = validated_function.dataset_codes - set(dataset_values.keys())
    if missing:
        raise ValueError(f"Missing dataset values: {missing}")

    # Build local namespace
    local_vars = dict(dataset_values)
    local_vars["Score"] = None

    # Add goalpost variables if needed
    if validated_function.uses_goalposts_as_vars:
        if lower_goalpost is not None:
            local_vars["LowerGoalpost"] = lower_goalpost
        if upper_goalpost is not None:
            local_vars["UpperGoalpost"] = upper_goalpost

    try:
        # Execute in restricted environment
        exec(validated_function.normalized, SAFE_GLOBALS, local_vars)
    except Exception as e:
        raise ScoreFunctionValidationError(
            f"Score function execution failed: {type(e).__name__}: {e}"
        )

    score = local_vars.get("Score")
    if score is None:
        raise ScoreFunctionValidationError(
            "Score function did not assign a value to Score"
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
