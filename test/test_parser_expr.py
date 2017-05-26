
import unittest
import itertools

import fix_import
from builder import *
import ast
import parser


class AstTester(unittest.TestCase):
    def __init__(self, *args, **kw):
        super(AstTester, self).__init__(*args, **kw)
        self._asserters = {
            ast.Group        : self._assertAst_Group,
            ast.MatchBegin   : self._assertAst_MatchBegin,
            ast.MatchEnd     : self._assertAst_MatchEnd,
            ast.Alternative  : self._assertAst_Alternative,
            ast.SingleChar   : self._assertAst_SingleChar,
            ast.PatternChar  : self._assertAst_PatternChar,
            ast.Range        : self._assertAst_Range,
            ast.CharClass    : self._assertAst_CharClass,
            ast.NoneOrOnce   : self._assertAst_NoneOrOnce,
            ast.NoneOrMore   : self._assertAst_NoneOrMore,
            ast.OneTime      : self._assertAst_OneTime,
            ast.OneOrMore    : self._assertAst_OneOrMore,
            ast.Between      : self._assertAst_Between
        }

    def assertAstEqual(self, ast, expected):
        self.assertEqual(type(ast), type(expected))
        self._asserters[type(ast)](ast, expected)

    def _assertAst_Group(self, group: ast.Group, expected: ast.Group):
        self.assertEqual(group.name, expected.name)
        self.assertEqual(group.ignored, expected.ignored)
        self.assertEqual(group.lookhead, expected.lookhead)
        self.assertAstEqual(group.quantifier, expected.quantifier)
        for (elem, elem_expected) in itertools.zip_longest(group.seq,
                                                           expected.seq):
            self.assertAstEqual(elem, elem_expected)

    def _assertAst_MatchBegin(self, _1, _2):
        pass

    def _assertAst_MatchEnd(self, _1, _2):
        pass

    def _assertAst_Alternative(self, alt: ast.Alternative,
                               expected: ast.Alternative):
        for (elem, elem_expected) in itertools.zip_longest(alt.parts,
                                                           expected.parts):
            self.assertAstEqual(elem, elem_expected)

    def _assertAst_SingleChar(self, singlechar: ast.SingleChar,
                              expected: ast.SingleChar):
        self.assertEqual(singlechar.char, expected.char)
        self.assertAstEqual(singlechar.quantifier, expected.quantifier)

    def _assertAst_PatternChar(self, pattern: ast.PatternChar,
                               expected: ast.PatternChar):
        self.assertEqual(pattern.pattern, expected.pattern)
        self.assertEqual(pattern.type, expected.type)
        self.assertAstEqual(pattern.quantifier, expected.quantifier)
        pass

    def _assertAst_Range(self, range_: ast.Range, expected: ast.Range):
        self.assertAstEqual(range_.begin, expected.begin)
        self.assertAstEqual(range_.end, expected.end)

    def _assertAst_CharClass(self, charclass: ast.CharClass,
                             expected: ast.CharClass):
        self.assertEqual(charclass.negate, expected.negate)
        self.assertAstEqual(charclass.quantifier, expected.quantifier)
        for (elem, elem_expected) in itertools.zip_longest(charclass.elems,
                                                           expected.elems):
            self.assertAstEqual(elem, elem_expected)

    def _assertAst_NoneOrOnce(self, _1, _2):
        pass

    def _assertAst_NoneOrMore(self, _1, _2):
        pass

    def _assertAst_OneTime(self, _1, _2):
        pass

    def _assertAst_OneOrMore(self, _1, _2):
        pass

    def _assertAst_Between(self, interval: ast.Between, expected: ast.Between):
        self.assertEqual(interval.min, expected.min)
        self.assertEqual(interval.max, expected.max)


    def _test_parse(self, input_expr, expected_ast):
        result = parser.parse(input_expr)
        self.assertAstEqual(result, expected_ast)


#-----------------------------------------------------------------------------
# Nominal cases
class TestBaseOfExpression(AstTester):
    def __init__(self, *args, **kw):
        super(TestBaseOfExpression, self).__init__(*args, **kw)

    def test_parse_sequence(self):
        self._test_parse(
            "aB",
            Expect().seq("a", "B").build()
        )

    def test_parse_character_class_individual(self):
        self._test_parse(
            "[aB]",
            Expect().chcls("a", "B").build()
        )

    def test_parse_number_range(self):
        self._test_parse(
            "[1-4]",
            Expect().numrng("1", "4").build()
        )

    def test_parse_character_range(self):
        self._test_parse(
            "[a-z]",
            Expect().chrng("a", "z").build()
        )

    def test_parse_avoid_character_class_individual(self):
        self._test_parse(
            "[^a]",
            Expect().chcls("a", negate=True).build()
        )

    def test_parse_avoid_range(self):
        self._test_parse(
            "[^B-C]",
            Expect().chrng("B", "C", negate=True).build()
        )

    def test_parse_single_special_char(self):
        special_chars = (
            "t",
            "n",
            "v",
            "f",
            "r",
            "0"
#            r"\x12",
#            r"\u0001"
        )
        for spc in special_chars:
            self._test_parse(
                "\\" + spc,
                Expect().pattch(spc).build()
            )

    def test_parse_range_special_char(self):
        special_chars = (
            "d",
            "D",
            "s",
            "S",
            "w",
            "W"
        )
        for spc in special_chars:
            self._test_parse(
                "\\" + spc,
                Expect().pattch(spc).build()
            )

    def test_parse_escaped_char(self):
        escaped_chars = (
            ".",
            "^",
            "$",
            "\\",
            "*",
            "+",
            "?",
            "(",
            ")",
            "[",
            "]",
            "{",
            "}",
            "|"
        )
        for ech in escaped_chars:
            self._test_parse(
                "\\" + ech,
                Expect().pattch(ech).build()
            )

    def test_parse_posix_classes(self):
        posix_classes = (
            "alnum",
            "alpha",
            "blank",
            "cntrl",
            "digit",
            "graph",
            "lower",
            "print",
            "punct",
            "space",
            "upper",
            "xdigit",
            "d",
            "w",
            "s",
        )
        for spc in posix_classes:
            self._test_parse(
                "[:{}:]".format(spc),
                Expect().pattch(spc, type=ast.PatternChar.Posix).build()
            )

    def test_parse_group(self):
        self._test_parse(
            "(a)",
            Expect().seq("a").close_group().build()
        )

    def test_parse_group_ignored(self):
        self._test_parse(
            "(?:a)",
            Expect().seq("a").close_group(ignored=True).build()
        )

    def test_parse_group_named(self):
        self._test_parse(
            "(?<name>a)",
            Expect().seq("a").close_group(name="name").build()
        )

    def test_parse_group_pos_lookhead(self):
        self._test_parse(
            "(?=a)",
            Expect().seq("a").close_group(lookhead=ast.Group.PositiveLookhead).build()
        )

    def test_parse_group_neg_lookhead(self):
        self._test_parse(
            "(?!a)",
            Expect().seq("a").close_group(lookhead=ast.Group.NegativeLookhead).build()
        )

    def test_parse_beginning_line(self):
        self._test_parse(
            "^a",
            Expect().bol().seq("a").build()
        )

    def test_parse_ending_line(self):
        self._test_parse(
            "a$",
            Expect().seq("a").eol().build()
        )

    def test_parse_alt(self):
        self._test_parse(
            "a|b",
            Expect().raw_alt(
                Expect().seq("a").ast[0],
                Expect().seq("b").ast[0]
            ).build()
        )

    def test_parse_quantifier_maybe_one(self):
        self._test_parse(
            "a?",
            Expect().seq("a").q_maybe().build()
        )

    def test_parse_quantifier_only_one(self):
        self._test_parse(
            "a",
            Expect().seq("a").q_1().build()
        )

    def test_parse_quantifier_one_or_more(self):
        self._test_parse(
            "a+",
            Expect().seq("a").q_1n().build()
        )

    def test_parse_quantifier_zero_or_more(self):
        self._test_parse(
            "a*",
            Expect().seq("a").q_0n().build()
        )

    def test_parse_repeat_from(self):
        self._test_parse(
            "a{1,}",
            Expect().seq("a").q_rng(1,None).build()
        )

    def test_parse_repeat_up_to(self):
        self._test_parse(
            "a{,2}",
            Expect().seq("a").q_rng(None,2).build()
        )

    def test_parse_repeat(self):
        self._test_parse(
            "a{1,2}",
            Expect().seq("a").q_rng(1,2).build()
        )

    def test_parse_quantifier_non_greedy(self):
        self._test_parse(
            "a+?",
            Expect().seq("a").q_1n(greedy=False).build()
        )


#-----------------------------------------------------------------------------
# Edge case
class TestOfCommonTrap(AstTester):
    def __init__(self, *args, **kw):
        super(TestOfCommonTrap, self).__init__(*args, **kw)

    def test_char_classes_with_posix_at_begin(self):
        self._test_parse(
            "[[:digit:]a]",
            Expect().chcls(
                Expect().pattch(":digit:").ast[0],
                Expect().seq("a").ast[0]
            ).build()
        )

    def test_char_classes_with_posix_at_end(self):
        self._test_parse(
            "[a[:digit:]]",
            Expect().chcls(
                Expect().seq("a").ast[0],
                Expect().pattch(":digit:").ast[0]
            ).build()
        )

    def test_char_classes_with_square_bracket(self):
        self._test_parse(
            "[\\]\\[]",
            Expect().chcls("]", "[").build()
        )

    def test_char_classes_with_caret_and_dollar(self):
        self._test_parse(
            "[$^]",
            Expect().chcls("$", "^").build()
        )

    def test_char_class_with_hypen(self):
        self._test_parse(
            "[a-b-]",
            Expect().chcls(
                Expect().raw_rng("a", "b").ast[0],
                Expect().seq("-").ast[0],
                dont_sequence=True
            ).build()
        )

    def test_not_a_range(self):
        self._test_parse(
            "a-b",
            Expect().seq("a", "-", "b").build()
        )

    def test_group_with_alt_not_captured(self):
        self._test_parse(
            "(?:a|\\?:b)",
            Expect().raw_alt(
                Expect().seq("a").ast[0],
                Expect().seq("?", ":", "b").ast
            ).close_group(ignored=True)
            .build()
        )


if __name__ == "__main__":
    unittest.main()
