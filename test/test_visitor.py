
import unittest

import fix_import
import builder as be
import ast


class CounterVisitor:
    def __init__(self):
        self.group = 0
        self.alt = 0
        self.range = 0
        self.match_begin = 0
        self.match_end = 0
        self.single_char = 0
        self.pattern_char = 0
        self.q_none_or_once = 0
        self.q_none_or_more = 0
        self.q_one_time = 0
        self.q_one_or_more = 0
        self.q_between = 0

    def visit_Group(self, group):
        self.group += 1

    def visit_Alternative(self, alt):
        self.alt += 1

    def visit_Range(self, range):
        self.range += 1

    def visit_MatchBegin(self, mb):
        self.match_begin += 1

    def visit_MatchEnd(self, me):
        self.match_end += 1

    def visit_SingleChar(self, sch):
        self.single_char += 1

    def visit_PatternChar(self, pch):
        self.pattern_char += 1

    def visit_NoneOrOnce(self, q):
        self.q_none_or_once += 1

    def visit_NoneOrMore(self, q):
        self.q_none_or_more += 1

    def visit_OneTime(self, q):
        self.q_one_time += 1

    def visit_OreOrMore(self, q):
        self.q_one_or_more += 1

    def visit_Between(self, btn):
        self.q_between += 1


class TestVisitor(unittest.TestCase):

    def test_quantifier_one_time(self):
        structs = (
            be.ch("a"),
            be.ch("\\x10"),
            be.ch("\\u1234"),
            be.ch("[a]"),
            be.ch("(a)"),
            be.ch("\w"),
            be.ch(".")
        )
        for st in structs:
            built_ast = be.grp(st)
            visitor = CounterVisitor()
            ast.visit(built_ast, visitor)
            self.assertEqual(visitor.q_one_time, 1)


if __name__ == "__main__":
    unittest.main()
