"""
Adversarial Security Tests for Score Function Validator

This module contains crafty attack attempts designed to probe for vulnerabilities
in the score function validator. These tests verify that the security measures
hold against sophisticated attack patterns.

Attack categories tested:
1. Unicode/encoding attacks (homoglyphs, zero-width chars, escapes)
2. Comment and string injection
3. Attribute access obfuscation
4. Operator and expression exploits
5. Resource exhaustion (DoS)
6. Variable shadowing and function redefinition
7. Python internals access attempts
8. Whitespace and control character injection
9. Scientific notation and number parsing edge cases
10. Multi-stage/chained attacks
"""

import pytest
import sys
import os

from sspi_flask_app.api.resources.score_function_validator import (
    validate_score_function,
    safe_eval,
    validate_and_execute,
    ScoreFunctionValidationError,
)


class TestUnicodeAndEncodingAttacks:
    """Attacks using Unicode tricks to bypass validation."""

    def test_homoglyph_import_cyrillic_i(self):
        """Cyrillic 'і' (U+0456) looks like Latin 'i' - try to spell 'import'."""
        # іmport (Cyrillic і)
        malicious = "Score = \u0456mport('os').system('id')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_homoglyph_exec_greek_e(self):
        """Greek 'ε' or other e-like characters."""
        # Try various e-homoglyphs
        homoglyphs = [
            "\u0435xec",  # Cyrillic е
            "\u03B5xec",  # Greek ε
            "ex\u0435c",  # Cyrillic е in middle
        ]
        for attempt in homoglyphs:
            malicious = f"Score = {attempt}('print(1)')"
            with pytest.raises(ScoreFunctionValidationError):
                validate_score_function(malicious)

    def test_zero_width_character_injection(self):
        """Zero-width characters between letters to break pattern matching."""
        zero_widths = [
            "\u200B",  # Zero-width space
            "\u200C",  # Zero-width non-joiner
            "\u200D",  # Zero-width joiner
            "\uFEFF",  # Byte order mark
        ]
        for zw in zero_widths:
            malicious = f"Score = im{zw}port('os')"
            with pytest.raises(ScoreFunctionValidationError):
                validate_score_function(malicious)

    def test_unicode_escape_in_identifier(self):
        """Try unicode escapes like \\u0069mport for 'import'."""
        # This tests if raw unicode escapes are processed
        malicious = "Score = \\u0069mport('os')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_fullwidth_characters(self):
        """Fullwidth Latin characters (U+FF00 range)."""
        # Fullwidth 'i' = U+FF49, etc.
        malicious = "Score = \uFF49\uFF4D\uFF50\uFF4F\uFF52\uFF54('os')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_combining_characters_overlay(self):
        """Combining characters that might be stripped."""
        # Try to hide characters under combining marks
        malicious = "Score = i\u0308mport('os')"  # ï but with combining diaeresis
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_right_to_left_override(self):
        """RTL override to visually hide malicious code."""
        # \u202E is RTL override
        malicious = "Score = goalpost(\u202Etropmi('os'), 0, 100)"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_mathematical_alphanumeric_symbols(self):
        """Mathematical italic/bold letters that look like normal letters."""
        # Mathematical italic 'i' = U+1D456
        malicious = "Score = \U0001D456mport('os')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)


class TestCommentAndStringInjection:
    """Attempts to inject comments or strings to hide code."""

    def test_hash_comment_injection(self):
        """Try to use # to comment out rest of line."""
        malicious = "Score = 1 # import os"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_multiline_string_triple_quote(self):
        """Try triple-quoted strings."""
        malicious = 'Score = """import os""" + goalpost(X, 0, 1)'
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_string_literal_single_quotes(self):
        """Single-quoted strings."""
        malicious = "Score = 'malicious' and goalpost(X, 0, 1)"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_string_literal_double_quotes(self):
        """Double-quoted strings."""
        malicious = 'Score = "malicious" and goalpost(X, 0, 1)'
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_raw_string_prefix(self):
        """r-strings."""
        malicious = "Score = r'test' + goalpost(X, 0, 1)"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_fstring_injection(self):
        """f-string for code execution."""
        malicious = "Score = f'{__import__(\"os\").system(\"id\")}'"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_byte_string(self):
        """b-strings."""
        malicious = "Score = b'test' + goalpost(X, 0, 1)"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)


class TestAttributeAccessObfuscation:
    """Attempts to access dangerous attributes."""

    def test_dunder_builtins_direct(self):
        """Direct __builtins__ access."""
        malicious = "Score = __builtins__['eval']('1+1')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_dunder_builtins_via_getattr(self):
        """Access via getattr pattern."""
        malicious = "Score = getattr(__builtins__, 'eval')('1')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_dunder_class_access(self):
        """Access __class__ to climb MRO."""
        malicious = "Score = (1).__class__.__bases__[0].__subclasses__()"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_dunder_mro_access(self):
        """Access __mro__ for class hierarchy."""
        malicious = "Score = ''.__class__.__mro__[1].__subclasses__()"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_dunder_globals_access(self):
        """Access __globals__ from function."""
        malicious = "Score = goalpost.__globals__['__builtins__']"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_dunder_code_access(self):
        """Access __code__ attribute."""
        malicious = "Score = goalpost.__code__.co_consts"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_dunder_dict_access(self):
        """Access __dict__ attribute."""
        malicious = "Score = type.__dict__['__subclasses__'](type)"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_dunder_import_function(self):
        """Direct __import__ call."""
        malicious = "Score = __import__('os').system('id')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_bracket_attribute_access(self):
        """Using brackets for attribute access."""
        malicious = "Score = vars()['__builtins__']"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_dot_attribute_access(self):
        """Dot notation for dangerous attributes."""
        malicious = "Score = os.system('id')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_nested_dunder_through_int(self):
        """Access dunders through integer object."""
        malicious = "Score = (1).__class__.__base__.__subclasses__()[104].__init__.__globals__"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)


class TestOperatorAndExpressionExploits:
    """Exploiting operators and expression parsing."""

    def test_walrus_operator_assignment(self):
        """Walrus operator := for assignment."""
        malicious = "Score = (x := __import__('os'))"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_list_comprehension(self):
        """List comprehension for code execution."""
        malicious = "Score = [x for x in [__import__('os')]][0]"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_dict_comprehension(self):
        """Dict comprehension."""
        malicious = "Score = {k:v for k,v in {'a':1}.items()}"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_set_comprehension(self):
        """Set comprehension."""
        malicious = "Score = {x for x in [1,2,3]}"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_generator_expression(self):
        """Generator expression."""
        malicious = "Score = next(x for x in [__import__('os')])"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_lambda_expression(self):
        """Lambda for code execution."""
        malicious = "Score = (lambda: __import__('os'))()"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_ternary_with_side_effect(self):
        """Ternary operator with side effects."""
        malicious = "Score = __import__('os') if True else 0"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_and_short_circuit(self):
        """Short-circuit evaluation for execution."""
        malicious = "Score = True and __import__('os')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_or_short_circuit(self):
        """Or short-circuit."""
        malicious = "Score = False or __import__('os')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_slice_notation(self):
        """Slice notation."""
        malicious = "Score = [1,2,3][0:2]"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_unpack_operator(self):
        """Unpacking operators * and **."""
        malicious = "Score = max(*[1,2,3])"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_matrix_multiplication_operator(self):
        """@ operator (could be overloaded)."""
        malicious = "Score = X @ Y"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)


class TestResourceExhaustion:
    """DoS attacks through resource consumption."""

    def test_deeply_nested_parentheses(self):
        """Deeply nested parentheses to exhaust parser."""
        depth = 1000
        malicious = "Score = " + "(" * depth + "1" + ")" * depth
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_deeply_nested_functions(self):
        """Deeply nested function calls."""
        depth = 100
        malicious = "Score = " + "goalpost(" * depth + "1, 0, 1" + ")" * depth
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_very_long_expression(self):
        """Very long expression (over max length)."""
        malicious = "Score = " + "1 + " * 1000 + "1"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_many_operators(self):
        """Many operators to slow parsing."""
        malicious = "Score = " + " + ".join(["1"] * 500)
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_exponential_computation(self):
        """Exponential that would take forever to compute - should be rejected."""
        # 10 ** 10 ** 10 would compute 10^(10^10) - a number with ~10 billion digits
        # This is a DoS attack and must be rejected at validation
        malicious = "Score = 10 ** 10 ** 10"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_safe_exponent_allowed(self):
        """Safe exponents under the limit should work using pow()."""
        # ** operator is now banned - use pow() for safe exponentiation
        safe = "Score = goalpost(X * pow(10, 8), 0, 1)"
        validated = validate_score_function(safe, {"X"})
        assert validated is not None

    def test_exponent_at_limit(self):
        """Exponent at the limit (10) should work using pow()."""
        safe = "Score = goalpost(pow(2, 10), 0, 100000)"
        validated = validate_score_function(safe)
        assert validated is not None

    def test_exponent_over_limit(self):
        """Exponent over limit (11) should be rejected."""
        # Using pow() - exponent exceeds MAX_EXPONENT_VALUE of 10
        malicious = "Score = goalpost(pow(2, 11), 0, 100)"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_recursive_average(self):
        """Try to create recursion through average."""
        # Can't actually recurse, but try many nested averages
        malicious = "Score = average(" + "average(" * 50 + "1, 2" + ")" * 50 + ", 3)"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)


class TestVariableShadowingAndRedefinition:
    """Attempts to shadow or redefine safe functions."""

    def test_redefine_goalpost(self):
        """Try to redefine goalpost function."""
        malicious = "goalpost = lambda x,y,z: __import__('os'); Score = goalpost(1,0,1)"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_shadow_score_variable(self):
        """Try multiple Score assignments."""
        malicious = "Score = 1; Score = __import__('os')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_redefine_average(self):
        """Try to redefine average."""
        malicious = "average = exec; Score = average('import os')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_redefine_max_min(self):
        """Try to redefine max/min."""
        malicious = "max = __import__; Score = max('os')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_del_statement(self):
        """Try del statement."""
        malicious = "del goalpost; Score = 1"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_global_statement(self):
        """Try global statement."""
        malicious = "global os; Score = 1"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_nonlocal_statement(self):
        """Try nonlocal statement."""
        malicious = "nonlocal x; Score = 1"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)


class TestPythonInternalsAccess:
    """Attempts to access Python internals."""

    def test_type_function(self):
        """Use type() to create classes."""
        malicious = "Score = type('X', (), {'__init__': lambda s: None})"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_eval_function(self):
        """Direct eval call."""
        malicious = "Score = eval('1+1')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_exec_function(self):
        """Direct exec call."""
        malicious = "Score = exec('x=1')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_compile_function(self):
        """compile() to create code objects."""
        malicious = "Score = compile('1', '', 'eval')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_open_function(self):
        """open() for file access."""
        malicious = "Score = open('/etc/passwd').read()"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_input_function(self):
        """input() function."""
        malicious = "Score = input('enter: ')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_print_function(self):
        """print() function (information disclosure)."""
        malicious = "Score = print('secret') or 1"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_breakpoint_function(self):
        """breakpoint() to drop into debugger."""
        malicious = "Score = breakpoint()"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_help_function(self):
        """help() function."""
        malicious = "Score = help()"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_dir_function(self):
        """dir() for introspection."""
        malicious = "Score = dir(__builtins__)"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_vars_function(self):
        """vars() to access namespace."""
        malicious = "Score = vars()['__builtins__']"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_locals_function(self):
        """locals() to access local namespace."""
        malicious = "Score = locals()['__builtins__']"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_globals_function(self):
        """globals() to access global namespace."""
        malicious = "Score = globals()['__builtins__']"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_memoryview(self):
        """memoryview for memory access."""
        malicious = "Score = memoryview(b'test')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_bytearray(self):
        """bytearray construction."""
        malicious = "Score = bytearray(b'test')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)


class TestWhitespaceAndControlCharacters:
    """Attacks using unusual whitespace and control characters."""

    def test_null_byte_injection(self):
        """Null byte to terminate string early."""
        malicious = "Score = 1\x00import os"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_vertical_tab(self):
        """Vertical tab as whitespace."""
        malicious = "Score\x0B=\x0B1"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_form_feed(self):
        """Form feed character."""
        malicious = "Score\x0C=\x0C1"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_carriage_return_injection(self):
        """Carriage return to hide code."""
        malicious = "Score = 1\rimport os"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_newline_injection(self):
        """Newline to add second statement."""
        malicious = "Score = 1\nimport os"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_line_separator(self):
        """Unicode line separator U+2028."""
        malicious = "Score = 1\u2028import os"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_paragraph_separator(self):
        """Unicode paragraph separator U+2029."""
        malicious = "Score = 1\u2029import os"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_nbsp_in_identifier(self):
        """Non-breaking space in identifier."""
        malicious = "Score = im\xa0port('os')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_tab_character_statement_separator(self):
        """Tab used to separate statements."""
        malicious = "Score = 1\t; import os"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)


class TestScientificNotationAndNumberEdgeCases:
    """Edge cases in number parsing."""

    def test_scientific_notation_large(self):
        """Very large exponent in scientific notation."""
        malicious = "Score = 1e309"  # Larger than max float
        try:
            validated = validate_score_function(malicious)
            result = safe_eval(validated, {})
            assert result == float('inf')
        except ScoreFunctionValidationError:
            pass  # Also acceptable

    def test_scientific_notation_small(self):
        """Very small exponent."""
        malicious = "Score = 1e-400"
        try:
            validated = validate_score_function(malicious)
            result = safe_eval(validated, {})
            assert result == 0.0
        except ScoreFunctionValidationError:
            pass

    def test_hex_notation(self):
        """Hexadecimal numbers."""
        malicious = "Score = 0xDEADBEEF"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_octal_notation(self):
        """Octal numbers."""
        malicious = "Score = 0o777"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_binary_notation(self):
        """Binary numbers."""
        malicious = "Score = 0b1010"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_complex_number(self):
        """Complex numbers."""
        malicious = "Score = 1+2j"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_underscore_in_number(self):
        """Underscores in numbers (Python 3.6+)."""
        malicious = "Score = 1_000_000"
        # This might be valid or invalid depending on tokenizer
        try:
            validated = validate_score_function(malicious)
            result = safe_eval(validated, {})
            assert result == 1000000
        except ScoreFunctionValidationError:
            pass  # Also acceptable if rejected

    def test_inf_literal(self):
        """Try to use inf directly."""
        malicious = "Score = inf"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_nan_literal(self):
        """Try to use nan directly."""
        malicious = "Score = nan"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)


class TestMultiStageAndChainedAttacks:
    """Complex attacks combining multiple techniques."""

    def test_nested_function_call_with_string_method(self):
        """Chain string methods."""
        malicious = "Score = 'os'.upper().__class__.__mro__[0]"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_arithmetic_then_attribute(self):
        """Arithmetic result then attribute access."""
        malicious = "Score = (1).__class__"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_nested_getattr_simulation(self):
        """Try to simulate getattr through bracket access."""
        malicious = "Score = {}.__class__.__bases__[0]"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_function_composition_attack(self):
        """Compose functions to bypass individual checks."""
        malicious = "Score = max(min(eval('1'), 2), 0)"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_exception_attribute_access(self):
        """Access attributes through exception handling."""
        malicious = "Score = Exception.__init__.__globals__"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_format_string_attribute_access(self):
        """Format strings to access attributes."""
        malicious = "Score = '{0.__class__}'.format(1)"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_method_chaining(self):
        """Method chaining attack."""
        malicious = "Score = [].append.__self__.__class__.__bases__"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_descriptor_protocol_abuse(self):
        """Abuse descriptor protocol."""
        malicious = "Score = type.__dict__['__subclasses__'].__get__(type)()"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)


class TestContextAndControlFlow:
    """Attempts using context managers and control flow."""

    def test_with_statement(self):
        """with statement for context managers."""
        malicious = "with open('/etc/passwd') as f: Score = f.read()"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_try_except(self):
        """try/except for exception handling."""
        malicious = "try: Score = 1/0\nexcept: Score = __import__('os')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_if_statement(self):
        """if statement."""
        malicious = "if True: Score = __import__('os')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_for_loop(self):
        """for loop."""
        malicious = "for x in [1]: Score = x"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_while_loop(self):
        """while loop."""
        malicious = "while True: Score = 1; break"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_assert_statement(self):
        """assert statement."""
        malicious = "assert False, __import__('os'); Score = 1"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_raise_statement(self):
        """raise statement."""
        malicious = "raise Exception(__import__('os')); Score = 1"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_yield_expression(self):
        """yield expression (generator)."""
        malicious = "Score = yield __import__('os')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_await_expression(self):
        """await expression (async)."""
        malicious = "Score = await some_async_func()"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_class_definition(self):
        """class definition."""
        malicious = "class Evil: pass; Score = 1"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_function_definition(self):
        """def statement."""
        malicious = "def evil(): return __import__('os'); Score = evil()"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_async_def(self):
        """async def."""
        malicious = "async def evil(): pass; Score = 1"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)


class TestEdgeCaseTokenization:
    """Edge cases in tokenization that might confuse the parser."""

    def test_multiple_equals(self):
        """Multiple equals signs."""
        malicious = "Score == 1"  # Comparison, not assignment
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_augmented_assignment(self):
        """Augmented assignment operators."""
        malicious = "Score += 1"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_chained_comparison(self):
        """Chained comparisons."""
        malicious = "Score = 1 < 2 < 3"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_not_operator(self):
        """not operator."""
        malicious = "Score = not False"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_in_operator(self):
        """in operator."""
        malicious = "Score = 1 in [1,2,3]"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_is_operator(self):
        """is operator."""
        malicious = "Score = 1 is 1"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_bitwise_operators(self):
        """Bitwise operators &, |, ^, ~."""
        operators = ["&", "|", "^"]
        for op in operators:
            malicious = f"Score = 1 {op} 2"
            with pytest.raises(ScoreFunctionValidationError):
                validate_score_function(malicious)

    def test_bitwise_not(self):
        """Bitwise not ~."""
        malicious = "Score = ~1"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_shift_operators(self):
        """Bit shift operators."""
        malicious = "Score = 1 << 10"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_floor_division(self):
        """Floor division //."""
        # This might be allowed or rejected
        malicious = "Score = goalpost(10 // 3, 0, 1)"
        try:
            validated = validate_score_function(malicious)
            # If allowed, verify it works correctly
            result = safe_eval(validated, {})
            assert 0 <= result <= 1
        except ScoreFunctionValidationError:
            pass  # Rejected is also fine

    def test_modulo_operator(self):
        """Modulo % operator."""
        malicious = "Score = goalpost(10 % 3, 0, 1)"
        try:
            validated = validate_score_function(malicious)
            result = safe_eval(validated, {})
            assert 0 <= result <= 1
        except ScoreFunctionValidationError:
            pass


class TestEnvironmentPollution:
    """Attempts to pollute the execution environment."""

    def test_modify_globals_dict(self):
        """Try to modify globals during execution."""
        malicious = "Score = 1; globals().update({'evil': True})"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_modify_locals_dict(self):
        """Try to modify locals during execution."""
        malicious = "Score = 1; locals()['evil'] = True"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_setattr_attack(self):
        """Use setattr to modify objects."""
        malicious = "setattr(__builtins__, 'evil', True); Score = 1"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_delattr_attack(self):
        """Use delattr to remove protections."""
        malicious = "delattr(type, '__subclasses__'); Score = 1"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)


class TestExecutionContextExploits:
    """Exploits targeting the safe_eval execution context."""

    def test_valid_then_malicious_in_datasets(self):
        """Inject malicious code through dataset values."""
        # This tests if dataset values can somehow be code-executed
        valid = "Score = goalpost(DATASET_A, 0, 100)"
        validated = validate_score_function(valid, {"DATASET_A"})

        # Now try to pass malicious data as "dataset value"
        # The value should be treated as a number, not code
        result = safe_eval(validated, {"DATASET_A": 50})
        assert result == 0.5

    def test_division_by_zero_handling(self):
        """Division by zero should be handled gracefully."""
        valid = "Score = goalpost(DATASET_A / DATASET_B, 0, 100)"
        validated = validate_score_function(valid, {"DATASET_A", "DATASET_B"})

        # Should handle division by zero gracefully
        try:
            result = safe_eval(validated, {"DATASET_A": 1, "DATASET_B": 0})
            # Either return inf or raise controlled exception
            assert result == float('inf') or result != result  # inf or nan
        except ZeroDivisionError:
            pass  # Also acceptable
        except Exception as e:
            # Should be a controlled exception, not arbitrary code execution
            assert "division" in str(e).lower() or "zero" in str(e).lower()

    def test_nan_input_rejected(self):
        """NaN values should raise an error, not silently produce wrong results."""
        valid = "Score = goalpost(DATASET_A, 0, 100)"
        validated = validate_score_function(valid, {"DATASET_A"})

        # NaN indicates data quality issue - fail fast with clear error
        with pytest.raises((ValueError, ScoreFunctionValidationError)):
            safe_eval(validated, {"DATASET_A": float('nan')})

    def test_inf_handling(self):
        """Infinity should be handled."""
        valid = "Score = goalpost(DATASET_A, 0, 100)"
        validated = validate_score_function(valid, {"DATASET_A"})

        result = safe_eval(validated, {"DATASET_A": float('inf')})
        # Should clamp to 1.0 or handle gracefully
        assert result == 1.0 or result == float('inf')

    def test_negative_inf_handling(self):
        """Negative infinity should be handled."""
        valid = "Score = goalpost(DATASET_A, 0, 100)"
        validated = validate_score_function(valid, {"DATASET_A"})

        result = safe_eval(validated, {"DATASET_A": float('-inf')})
        # Should clamp to 0.0 or handle gracefully
        assert result == 0.0 or result == float('-inf')


class TestRegressionFromRealAttacks:
    """Test patterns from known real-world Python sandbox escapes."""

    def test_pyjail_classic_subclass_attack(self):
        """Classic pyjail escape: find 'os' module through subclasses."""
        malicious = "Score = ''.__class__.__mro__[2].__subclasses__()[40]('/etc/passwd').read()"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_pyjail_warnings_catch_warnings(self):
        """warnings.catch_warnings has linecache which has os."""
        malicious = "Score = [x for x in ().__class__.__bases__[0].__subclasses__() if 'warning' in str(x)][0]()._module.__builtins__['__import__']('os').system('id')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_pyjail_codecs_attack(self):
        """codecs.open for file access."""
        malicious = "Score = [x for x in ().__class__.__bases__[0].__subclasses__() if 'codec' in str(x).lower()][0]"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_pickle_loads_attack(self):
        """pickle.loads for code execution."""
        malicious = "Score = __import__('pickle').loads(b'...')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_subprocess_attack(self):
        """subprocess module."""
        malicious = "Score = __import__('subprocess').check_output(['id'])"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_ctypes_attack(self):
        """ctypes for arbitrary memory access."""
        malicious = "Score = __import__('ctypes').CDLL('libc.so.6').system('id')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)

    def test_builtins_recovery_via_exception(self):
        """Recover builtins from exception traceback."""
        malicious = "Score = [x for x in (1).__class__.__base__.__subclasses__() if x.__name__=='Sized'][0].__len__.__globals__['__builtins__']['eval']('1')"
        with pytest.raises(ScoreFunctionValidationError):
            validate_score_function(malicious)
