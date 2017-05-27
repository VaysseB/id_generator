
import unittest
import itertools

import fix_import
import builder as be
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
        paired_parts = itertools.zip_longest(alt.parts, expected.parts)
        for (part, part_expected) in paired_parts:
            self.assertIsNotNone(part)
            self.assertIsNotNone(part_expected)

            paired_elems = itertools.zip_longest(part, part_expected)
            for (elem, elem_expected) in paired_elems:
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

    def _test_parse(self, input_expr: str, expected: tuple):
        result = parser.parse(input_expr)
        expected_ast = be.grp(*expected)
        self.assertAstEqual(result, expected_ast)


#-----------------------------------------------------------------------------
# Nominal cases
class TestBaseOfExpression(AstTester):
    def __init__(self, *args, **kw):
        super(TestBaseOfExpression, self).__init__(*args, **kw)

    def test_parse_sequence(self):
        self._test_parse(
            "aB",
            (be.ch("a"), be.ch("B"))
        )

    def test_parse_character_class_individual(self):
        self._test_parse(
            "[aB]",
            (be.class_(be.ch("a"), be.ch("B")),)
        )

    def test_parse_number_range(self):
        self._test_parse(
            "[1-4]",
            (be.class_(be.rang_ch("1", "4")),)
        )

    def test_parse_character_range(self):
        self._test_parse(
            "[a-z]",
            (be.class_(be.rang_ch("a", "z")),)
        )

    def test_parse_avoid_character_class_individual(self):
        self._test_parse(
            "[^a]",
            (be.class_(be.ch("a"), reverse=True),)
        )

    def test_parse_avoid_range(self):
        self._test_parse(
            "[^B-C]",
            (be.class_(be.rang_ch("B", "C"), reverse=True),)
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
                (be.ptrn(spc),)
            )

    def test_parse_ascii_char(self):
        ascii_chars = (
            "12",
            "AF"
        )
        for ach in ascii_chars:
            self._test_parse(
                "\\x" + ach,
                (be.ptrn(ach, type=ast.PatternChar.Ascii),)
            )

    def test_parse_unicode_char(self):
        unicode_chars = (
            "138A",
            "983F"
        )
        for ach in unicode_chars:
            self._test_parse(
                "\\u" + ach,
                (be.ptrn(ach, type=ast.PatternChar.Unicode),)
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
                (be.ptrn(spc),)
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
                (be.ch(ech),)
            )

    def test_parse_escaped_char_in_class(self):
        escaped_chars = (
            "\\",
            "[",
            "]"
        )
        for ech in escaped_chars:
            self._test_parse(
                "[\\" + ech + "]",
                (be.class_(be.ch(ech)),)
            )

    def test_parse_dot_as_generic(self):
        self._test_parse(
            ".",
            (be.ptrn("."),)
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
                (be.ptrn(spc, type=ast.PatternChar.Posix),)
            )

    def test_parse_group(self):
        self._test_parse(
            "(a)",
            (be.grp(be.ch("a")),)
        )

    def test_parse_group_ignored(self):
        self._test_parse(
            "(?:a)",
            (be.grp(be.ch("a"), ign=True),)
        )

    def test_parse_group_named(self):
        self._test_parse(
            "(?<name>a)",
            (be.grp(be.ch("a"), name="name"),)
        )

    def test_parse_group_pos_lookhead(self):
        self._test_parse(
            "(?=a)",
            (be.grp(be.ch("a"), lkhead=ast.Group.PositiveLookhead),)
        )

    def test_parse_group_neg_lookhead(self):
        self._test_parse(
            "(?!a)",
            (be.grp(be.ch("a"), lkhead=ast.Group.NegativeLookhead),)
        )

    def test_parse_beginning_line(self):
        self._test_parse(
            "^a",
            (be.bol(), be.ch("a"))
        )

    def test_parse_ending_line(self):
        self._test_parse(
            "a$",
            (be.ch("a"), be.eol())
        )

    def test_parse_alt(self):
        self._test_parse(
            "a|b",
            (be.alt(
                (be.ch("a"),),
                (be.ch("b"),)
            ),)
        )

    def test_parse_quantifier_maybe_one(self):
        self._test_parse(
            "a?",
            (be.ch("a", quant="?"),)
        )

    def test_parse_quantifier_only_one(self):
        self._test_parse(
            "a",
            (be.ch("a", quant="1"),)
        )

    def test_parse_quantifier_one_or_more(self):
        self._test_parse(
            "a+",
            (be.ch("a", quant="+"),)
        )

    def test_parse_quantifier_zero_or_more(self):
        self._test_parse(
            "a*",
            (be.ch("a", quant="*"),)
        )

    def test_parse_repeat_from(self):
        self._test_parse(
            "a{1,}",
            (be.ch("a", quant="1,"),)
        )

    def test_parse_repeat_up_to(self):
        self._test_parse(
            "a{,2}",
            (be.ch("a", quant=",2"),)
        )

    def test_parse_repeat(self):
        self._test_parse(
            "a{1,2}",
            (be.ch("a", quant="1,2"),)
        )

    def test_parse_quantifier_non_greedy_maybe_one(self):
        self._test_parse(
            "a??",
            (be.ch("a", quant="??"),)
        )

    def test_parse_quantifier_non_greedy_one_or_more(self):
        self._test_parse(
            "a+?",
            (be.ch("a", quant="+?"),)
        )

    def test_parse_quantifier_non_greedy_zero_or_more(self):
        self._test_parse(
            "a*?",
            (be.ch("a", quant="*?"),)
        )

    def test_parse_repeat_non_greedy(self):
        self._test_parse(
            "a{1,2}?",
            (be.ch("a", quant="1,2?"),)
        )


#-----------------------------------------------------------------------------
# Edge case
class TestOfCommonTrap(AstTester):
    def __init__(self, *args, **kw):
        super(TestOfCommonTrap, self).__init__(*args, **kw)

    def test_char_classes_with_posix_at_begin(self):
        self._test_parse(
            "[[:digit:]a]",
            (be.class_(
                be.ptrn("digit", type=ast.PatternChar.Posix),
                be.ch("a")
            ),)
        )

    def test_char_classes_with_posix_at_end(self):
        self._test_parse(
            "[a[:digit:]]",
            (be.class_(
                be.ch("a"),
                be.ptrn("digit", type=ast.PatternChar.Posix)
            ),)
        )

    def test_char_classes_with_square_bracket(self):
        self._test_parse(
            "[\\]\\[]",
            (be.class_(
                be.ch("]"),
                be.ch("[")
            ),)
        )

    def test_char_classes_with_caret_and_dollar(self):
        self._test_parse(
            "[$^]",
            (be.class_(
                be.ch("$"),
                be.ch("^")
            ),)
        )

    def test_char_class_only_with_hypen(self):
        self._test_parse(
            "[-]",
            (be.class_(
                be.ch("-")
            ),)
        )

    def test_char_class_with_hypen(self):
        self._test_parse(
            "[a-b-]",
            (be.class_(
                be.rang_ch("a", "b"),
                be.ch("-")
            ),)
        )

    def test_not_a_range(self):
        self._test_parse(
            "a-b",
            (be.ch("a"), be.ch("-"), be.ch("b"))
        )

    def test_group_with_alt_not_captured(self):
        self._test_parse(
            "(?:a|\\?:b)",
            (be.grp(
                be.alt(
                    (be.ch("a"),),
                    (be.ch("?"), be.ch(":"), be.ch("b"))
                ),
                ign=True
            ),)
        )


if __name__ == "__main__":
    unittest.main()
