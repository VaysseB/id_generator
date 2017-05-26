
import string

import ast
from state_machine import PSM, Source




class SpecialPattern:
    individual_chars = ('t', 'n', 'v', 'f', 'r', '0')
    range_chars = ('d', 'D', 'w', 'W', 's', 'S')
    special_chars = ('^', '$', '[', ']', '(', ')', '{', '}', '\\', '.', '*',
                     '?', '+', '|')
    restrict_special_chars = ('\\', '[', ']')
    posix_classes = ("alnum", "alpha", "blank", "cntrl", "digit", "graph",
                     "lower", "print", "punct", "space", "upper", "xdigit",
                     "d", "w", "s")
    min_len_posix_class = 1


#-------------------------------------
# Group

class OpeningOfGroup:
    def __init__(self, initial=False, prev=None):
        self.is_initial = initial
        self.prev = prev
        self.ast = ast.Group()
        self.content_of_initial = ContentOfGroup(self, initial) if initial else None

    def next(self, psm: PSM):
        if not self.is_initial and psm.char == "?":
            return FirstOptionOfGroup(self)
        elif psm.char == ")":
            if self.is_initial:
                psm.error = 'unexpected ")"'
            else:
                return self.prev
        elif psm.char == "(":
            g = OpeningOfGroup(prev=self)
            self.add_ast(g)
            return g
        elif self.is_initial:
            return self.content_of_initial.next(psm)
        else:
            c = ContentOfGroup(self)
            return c.next(psm)

    def add_ast(self, other):
        self.add(other.ast)

    def add(self, other):
        self.ast.seq = self.ast.seq + (other,)


class FirstOptionOfGroup:
    def __init__(self, group: OpeningOfGroup):
        self.group = group

    def next(self, psm: PSM):
        if psm.char == ":":
            self.group.ast.ignored = True
            return ContentOfGroup(self.group)
        elif psm.char == "!":
            self.group.ast.lookhead = ast.Group.NegativeLookhead
            return ContentOfGroup(self.group)
        elif psm.char == "=":
            self.group.ast.lookhead = ast.Group.PositiveLookhead
            return ContentOfGroup(self.group)
        elif psm.char == "<":
            self.group.ast.name = ""
            return NameOfGroup(self.group)

        psm.error = 'expected ":", "!", "<" or "="'


class NameOfGroup:
    def __init__(self, group: OpeningOfGroup):
        self.group = group

    def next(self, psm: PSM):
        if psm.char.isalpha() or psm.char == "_":
            self.group.ast.name += psm.char
            return self
        elif psm.char == ">":
            return self.group

        psm.error = 'expected a letter, "_" or ">"'


class ContentOfGroup:
    NotQuantified = 0
    Quantified = 1
    UngreedyQuantified = 2

    def __init__(self, group: OpeningOfGroup, initial: bool=False):
        self.group = group
        self.is_initial = initial
        self.prev = group if initial else self
        self.quantified = ContentOfGroup.NotQuantified # true if last consumed char was a quantifier

    def add(self, other):
        self.group.add(other)

    def next(self, psm: PSM):
        quantified = self.quantified
        self.quantified = ContentOfGroup.NotQuantified

        if psm.char == ")":
            if self.is_initial:
                psm.error = "unbalanced parenthesis"
            else:
                return self.group.prev

        elif psm.char == "(":
            g = OpeningOfGroup(prev=self.prev)
            self.group.add_ast(g)
            return g

        elif psm.char == "^":
            self.group.add(ast.MatchBegin())
            return self.prev

        elif psm.char == "$":
            self.group.add(ast.MatchEnd())
            return self.prev

        elif psm.char == "\\":
            g = EscapedChar(prev=self.prev,
                            as_single_chars=SpecialPattern.special_chars)
            return g

        elif psm.char == "[":
            r = CharClass(prev=self.prev)
            return r

        # >>> Quantifiers
        elif psm.char == "?" and quantified == ContentOfGroup.NotQuantified:
            self.quantified = ContentOfGroup.Quantified
            last = self._last_or_fail(psm)
            if last:
                last.quantifier = ast.NoneOrOnce()
            return self.prev

        elif psm.char == "*" and quantified == ContentOfGroup.NotQuantified:
            self.quantified = ContentOfGroup.Quantified
            last = self._last_or_fail(psm)
            if last:
                last.quantifier = ast.NoneOrMore()
            return self.prev

        elif psm.char == "+" and quantified == ContentOfGroup.NotQuantified:
            self.quantified = ContentOfGroup.Quantified
            last = self._last_or_fail(psm)
            if last:
                last.quantifier = ast.OneOrMore()
            return self.prev

        elif psm.char == "{" and quantified == ContentOfGroup.NotQuantified:
            self.quantified = ContentOfGroup.Quantified
            r = MinimumOfRepetition(prev=self.prev)
            last = self._last_or_fail(psm)
            if last:
                last.quantifier = r.ast
            return r

        elif psm.char == "?" and quantified == ContentOfGroup.Quantified:
            self.quantified = ContentOfGroup.UngreedyQuantified
            last = self._last_or_fail(psm)
            if last:
                last.quantifier.greedy = False
            return self.prev

        elif quantified == ContentOfGroup.Quantified:
            psm.error = "unexpected quantifier"

        elif quantified == ContentOfGroup.UngreedyQuantified:
            psm.error = "quantifier repeated"
        # <<< Quantifier

        else:
            c = ast.SingleChar()
            c.char = psm.char
            self.group.add(c)
            return self.prev

    def _last_or_fail(self, psm: PSM):
        if self.group.ast.seq:
            return self.group.ast.seq[-1]
        else:
            psm.error = "nothing to repeat"


class MinimumOfRepetition:
    def __init__(self, prev: ContentOfGroup):
        self.prev = prev
        self.ast = ast.Between()
        self.min = []

    def next(self, psm: PSM):
        if psm.char.isdigit():
            self.min.append(psm.char)
            return self
        elif psm.char == ",":
            self._interpret()
            return MaximumOfRepetition(prev=self.prev, ast=self.ast)
        elif psm.char == "}":
            self._interpret()
            return self.prev
        else:
            psm.error = 'expected digit, "," or "}"'

    def _interpret(self):
        if not self.min:
            return

        try:
            count = int("".join(self.min))
        except ValueError:
            assert False, "internal error: cannot convert to number"
        self.ast.min = count


class MaximumOfRepetition:
    def __init__(self, prev: ContentOfGroup, ast: ast.Between):
        self.prev = prev
        self.ast = ast
        self.max = []

    def next(self, psm: PSM):
        if psm.char.isdigit():
            self.max.append(psm.char)
            return self
        elif psm.char == "}":
            self._interpret()
            return self.prev
        else:
            psm.error = 'expected digit, "," or "}"'

    def _interpret(self):
        if not self.max:
            return

        try:
            count = int("".join(self.max))
        except ValueError:
            assert False, "internal error: cannot convert to number"
        self.ast.max = count


#--------------------------------------
class EscapedChar:
    def __init__(self, prev, as_single_chars):
        self.prev = prev  # ContentOfGroup or CharClass
        self.ast = ast.PatternChar()
        self.single_chars = as_single_chars

    def next(self, psm: PSM):
        if psm.char in SpecialPattern.individual_chars \
           or psm.char in SpecialPattern.range_chars:
            self.ast.pattern = psm.char
            self.prev.add(self.ast)
            return self
        elif psm.char in self.single_chars:
            self.ast = ast.SingleChar()
            self.ast.char = psm.char
            self.prev.add(self.ast)
            return self.prev
        elif psm.char == "x":
            self.prev.add(self.ast)
            return AsciiChar(self)
        elif psm.char == "u":
            self.prev.add(self.ast)
            return UnicodeChar(self)
        else:
            psm.error = "unauthorized escape of {}".format(psm.char)


class AsciiChar:
    def __init__(self, ech: EscapedChar):
        self.ech = ech
        self.ech.ast.type = ast.PatternChar.Ascii

    def next(self, psm: PSM):
        if psm.char in string.hexdigits:
            self.ech.ast.pattern += psm.char
            count = len(self.ech.ast.pattern)
            return self.ech.prev if count >= 2 else self
        else:
            psm.error = "expected ASCII letter or digit"


class UnicodeChar:
    def __init__(self, ech: EscapedChar):
        self.ech = ech
        self.ech.ast.type = ast.PatternChar.Unicode

    def next(self, psm: PSM):
        if psm.char in string.hexdigits:
            self.ech.ast.pattern += psm.char
            count = len(self.ech.ast.pattern)
            return self.ech.prev if count >= 4 else self
        else:
            psm.error = "expected ASCII letter or digit"


#-------------------------------------
class CharClass:
    def __init__(self, prev):
        self.prev = prev # ContentOfGroup or CharClass
        self.ast = ast.CharClass()
        self.next_is_range = False
        self.empty = True
        self.can_mutate = True

    def next(self, psm: PSM):
        this_should_be_range = self.next_is_range
        self.next_is_range = False

        this_is_empty = self.empty
        self.empty = False

        if psm.char == "\\":
            self.can_mutate = False
            self.next_is_range = this_should_be_range

            s = EscapedChar(prev=self,
                            as_single_chars=SpecialPattern.restrict_special_chars)
            return s

        elif this_should_be_range and psm.char != "]":
            self.next_is_range = False
            r = ast.Range()
            r.begin = self.ast.elems[-1]
            r.end = ast.SingleChar()
            r.end.char = psm.char
            self.swap_last(r)
            return self

        elif psm.char == "^":
            # if at the begining, it has a special meaning
            if this_is_empty:
                self.can_mutate = False
                self.ast.negate = True
            else:
                s = ast.SingleChar()
                s.char = psm.char
                self.add(s)
            return self

        elif psm.char == "]":
            if this_should_be_range:
                s = ast.SingleChar()
                s.char = "-"
                self.add(s)
            else:
                self.mutate_if_posix_like()

            self.prev.add(self.ast)
            return self.prev

        elif psm.char == "[":
            c = CharClass(prev=self)
            return c

        elif psm.char == "-" and len(self.ast.elems) >= 1:
            self.next_is_range = True
            return self

        else:
            s = ast.SingleChar()
            s.char = psm.char
            self.add(s)
            return self

    def add(self, other):
        self.ast.elems = self.ast.elems + (other,)

    def swap_last(self, other):
        self.ast.elems = self.ast.elems[:-1] + (other,)

    def mutate_if_posix_like(self):
        """
        Change from character class to pattern char if the content is matching
        POSIX-like classe.
        """
        # put in this variable everything that had happen but not saved into
        # the single char object
        # because mutation is only possible if the exact string of the content
        # match a pre-definied list, so if an unlogged char is consumed, it
        # must prevent mutation
        if not self.can_mutate:
            return

        if len(self.ast.elems) < SpecialPattern.min_len_posix_class + 2:
            return

        opening = self.ast.elems[0]
        if not isinstance(opening, ast.SingleChar) or opening.char != ":":
            return

        closing = self.ast.elems[-1]
        if not isinstance(closing, ast.SingleChar) or closing.char != ":":
            return

        is_only_ascii = lambda x: (isinstance(x, ast.SingleChar)
                                   and len(x.char) == 1
                                   and x.char.isalpha())
        class_may_be_a_word = not any(
            not is_only_ascii(x) for x in self.ast.elems[1:-1])
        if not class_may_be_a_word:
            return

        word = "".join(s.char for s in self.ast.elems[1:-1])
        if word not in SpecialPattern.posix_classes:
            return

        p = ast.PatternChar()
        p.pattern = word
        p.type = ast.PatternChar.Posix
        self.ast = p


#-------------------------------------
def parse(expr, **kw):
    sm = PSM()
    sm.source = Source(expr)
    sm.starts_with(OpeningOfGroup(initial=True))
    sm.pre_action = kw.get("pre_action", None)
    sm.post_action = kw.get("post_action", None)
    sm.parse()
    return sm.state.ast
