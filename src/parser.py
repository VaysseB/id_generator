
import string

import ast
from state_machine import PSM, Source



class SpecialPattern:
    individual_chars = ('t', 'n', 'v', 'f', 'r', '0')
    range_chars = ('d', 'D', 'w', 'W', 's', 'S')

    special_chars = ('^', '$', '[', ']', '(', ')', '{', '}', '\\', '.', '*',
                     '?', '+', '|', '.')
    restrict_special_chars = ('\\', '[', ']')

    posix_classes = ("alnum", "alpha", "blank", "cntrl", "digit", "graph",
                     "lower", "print", "punct", "space", "upper", "xdigit",
                     "d", "w", "s")
    min_len_posix_class = 1


#-------------------------------------
# Group

class WrappedGroup:
    def __init__(self):
        self.group = ast.Group()
        self.is_alt = False

    def add(self, other):
        if self.is_alt:
            last_alt = self.alt.parts[-1] + (other,)
            self.alt.parts = self.alt.parts[:-1] + (last_alt,)
        else:
            self.group.seq = self.group.seq + (other,)

    @property
    def alt(self) -> ast.Alternative:
        assert self.is_alt
        return self.group.seq[0]

    def collapse_alt(self):
        if self.is_alt:
            self.alt.parts = self.alt.parts + ((),)
        else:
            self.is_alt = True
            first_alt_elems = self.group.seq
            self.group.seq = (ast.Alternative(),)
            self.alt.parts = (first_alt_elems,())


class OpeningOfGroup:
    def __init__(self, parent: None, initial: bool=False):
        self.is_initial = initial
        self.parent = parent  # OpeningOfGroup or ContentOfGroup
        self.g = WrappedGroup()
        self.content_of_initial = None

        # forward of function
        self.add = self.g.add

        # if this group is the initial, their is no parent but we must refer
        # to itself as the returning state
        # but if it is a nested group, it must be added into its global group
        if self.is_initial:
            self.content_of_initial = ContentOfGroup(self, initial)
        else:
            self.parent.add(self.g.group)

    def next(self, psm: PSM):
        if not self.is_initial and psm.char == "?":
            return FirstOptionOfGroup(self)
        elif psm.char == ")":
            if self.is_initial:
                psm.error = 'unexpected ")"'
            else:
                return self.parent
        elif psm.char == "(":
            return OpeningOfGroup(self)
        elif self.is_initial:
            return self.content_of_initial.next(psm)
        else:
            t = ContentOfGroup(self)
            return t.next(psm)


class FirstOptionOfGroup:
    def __init__(self, parent: OpeningOfGroup):
        self.parent = parent

    def next(self, psm: PSM):
        if psm.char == ":":
            self.parent.g.group.ignored = True
            return ContentOfGroup(self.parent)
        elif psm.char == "!":
            self.parent.g.group.lookhead = ast.Group.NegativeLookhead
            return ContentOfGroup(self.parent)
        elif psm.char == "=":
            self.parent.g.group.lookhead = ast.Group.PositiveLookhead
            return ContentOfGroup(self.parent)
        elif psm.char == "<":
            self.parent.g.group.name = ""
            return NameOfGroup(self.parent)
        else:
            psm.error = 'expected ":", "!", "<" or "="'


class NameOfGroup:
    def __init__(self, parent: OpeningOfGroup):
        self.parent = parent

    def next(self, psm: PSM):
        if psm.char.isalpha() or psm.char == "_":
            self.parent.g.group.name += psm.char
            return self
        elif psm.char == ">":
            return self.parent
        else:
            psm.error = 'expected a letter, "_" or ">"'


class ContentOfGroup:
    NotQuantified = 0
    Quantified = 1
    UngreedyQuantified = 2

    def __init__(self, parent: OpeningOfGroup, initial: bool=False):
        self.parent = parent
        self.is_initial = initial
        self.limited_prev = parent if initial else self
        self.quantified = ContentOfGroup.NotQuantified

        # forward of function
        self.add = self.parent.add

    def next(self, psm: PSM):
        quantified = self.quantified
        self.quantified = ContentOfGroup.NotQuantified

        if psm.char == ")":
            if self.is_initial:
                psm.error = "unbalanced parenthesis"
            else:
                return self.parent.parent

        elif psm.char == "(":
            return OpeningOfGroup(self.limited_prev)

        elif psm.char == "^":
            self.add(ast.MatchBegin())
            return self.limited_prev

        elif psm.char == "$":
            self.add(ast.MatchEnd())
            return self.limited_prev

        elif psm.char == ".":
            t = ast.PatternChar()
            t.pattern = psm.char
            self.add(t)
            return self.limited_prev

        elif psm.char == "\\":
            return EscapedChar(self.limited_prev,
                               as_single_chars=SpecialPattern.special_chars)

        elif psm.char == "[":
            return CharClass(self.limited_prev)

        elif psm.char == "|":
            self.parent.g.collapse_alt()
            return self.limited_prev

        # >>> Quantifiers
        elif psm.char == "?" and quantified == ContentOfGroup.NotQuantified:
            self.quantified = ContentOfGroup.Quantified
            last = self._last_or_fail(psm)
            if last:
                last.quantifier = ast.NoneOrOnce()
            return self.limited_prev

        elif psm.char == "*" and quantified == ContentOfGroup.NotQuantified:
            self.quantified = ContentOfGroup.Quantified
            last = self._last_or_fail(psm)
            if last:
                last.quantifier = ast.NoneOrMore()
            return self.limited_prev

        elif psm.char == "+" and quantified == ContentOfGroup.NotQuantified:
            self.quantified = ContentOfGroup.Quantified
            last = self._last_or_fail(psm)
            if last:
                last.quantifier = ast.OneOrMore()
            return self.limited_prev

        elif psm.char == "{" and quantified == ContentOfGroup.NotQuantified:
            self.quantified = ContentOfGroup.Quantified
            t = MinimumOfRepetition(self.limited_prev)
            last = self._last_or_fail(psm)
            if last:
                last.quantifier = t.between
            return t

        elif psm.char == "?" and quantified == ContentOfGroup.Quantified:
            self.quantified = ContentOfGroup.UngreedyQuantified
            last = self._last_or_fail(psm)
            if last:
                last.quantifier.greedy = False
            return self.limited_prev

        elif quantified == ContentOfGroup.Quantified:
            psm.error = "unexpected quantifier"

        elif quantified == ContentOfGroup.UngreedyQuantified:
            psm.error = "quantifier repeated"
        # <<< Quantifier

        else:
            t = ast.SingleChar()
            t.char = psm.char
            self.add(t)
            return self.limited_prev

    def _last_or_fail(self, psm: PSM):
        if self.parent.g.group.seq:
            return self.parent.g.group.seq[-1]
        else:
            psm.error = "nothing to repeat"


class MinimumOfRepetition:
    def __init__(self, parent: ContentOfGroup):
        self.parent = parent
        self.between = ast.Between()
        self.min = []

    def next(self, psm: PSM):
        if psm.char.isdigit():
            self.min.append(psm.char)
            return self
        elif psm.char == ",":
            self._interpret()
            return MaximumOfRepetition(self)
        elif psm.char == "}":
            self._interpret()
            return self.parent
        else:
            psm.error = 'expected digit, "," or "}"'

    def _interpret(self):
        if not self.min:
            return

        try:
            count = int("".join(self.min))
        except ValueError:
            assert False, "internal error: cannot convert to number minimum of repetition"
        self.between.min = count


class MaximumOfRepetition:
    def __init__(self, repeat: MinimumOfRepetition):
        self.repeat = repeat
        self.max = []

    def next(self, psm: PSM):
        if psm.char.isdigit():
            self.max.append(psm.char)
            return self
        elif psm.char == "}":
            self._interpret()
            return self.repeat.parent
        else:
            psm.error = 'expected digit, "," or "}"'

    def _interpret(self):
        if not self.max:
            return

        try:
            count = int("".join(self.max))
        except ValueError:
            assert False, "internal error: cannot convert to number maximum of repetition"
        self.repeat.between.max = count


#--------------------------------------
# Escaping

class EscapedChar:
    def __init__(self, prev, as_single_chars=(), as_pattern_chars=()):
        self.prev = prev  # ContentOfGroup or CharClass
        self.single_chars = as_single_chars
        self.pattern_chars = as_pattern_chars

    def next(self, psm: PSM):
        if psm.char in SpecialPattern.individual_chars \
           or psm.char in SpecialPattern.range_chars \
           or psm.char in self.pattern_chars:
            t = ast.PatternChar()
            t.pattern = psm.char
            self.prev.add(t)
            return self.prev
        elif psm.char in self.single_chars:
            t = ast.SingleChar()
            t.char = psm.char
            self.prev.add(t)
            return self.prev
        elif psm.char == "x":
            return AsciiChar(self.prev)
        elif psm.char == "u":
            return UnicodeChar(self.prev)
        else:
            psm.error = "unauthorized escape of {}".format(psm.char)


class AsciiChar:
    def __init__(self, prev):
        self.prev = prev  # ContentOfGroup or CharClass
        self.pattern = ast.PatternChar()
        self.pattern.type = ast.PatternChar.Ascii

        self.prev.add(self.pattern)

    def next(self, psm: PSM):
        if psm.char in string.hexdigits:
            self.pattern.pattern += psm.char
            count = len(self.pattern.pattern)
            return self.prev if count >= 2 else self
        else:
            psm.error = "expected ASCII hexadecimal character"


class UnicodeChar:
    def __init__(self, prev):
        self.prev = prev  # ContentOfGroup or CharClass
        self.pattern = ast.PatternChar()
        self.pattern.type = ast.PatternChar.Unicode

        self.prev.add(self.pattern)

    def next(self, psm: PSM):
        if psm.char in string.hexdigits:
            self.pattern.pattern += psm.char
            count = len(self.pattern.pattern)
            return self.prev if count >= 4 else self
        else:
            psm.error = "expected ASCII hexadecimal character"


#-------------------------------------
# Character class

class WrappedCharClass:
    def __init__(self):
        # ast is CharClass or may be changed to PatternClass in one case
        self.ast = ast.CharClass()

    def add(self, other):
        assert isinstance(self.ast, ast.CharClass)
        self.ast.elems = self.ast.elems + (other,)

    def pop(self):
        assert isinstance(self.ast, ast.CharClass)
        last = self.ast.elems[-1]
        self.ast.elems = self.ast.elems[:-1]
        return last


class CharClass:
    def __init__(self, prev):
        self.prev = prev  # ContentOfGroup or CharClass
        self.q = WrappedCharClass()

        # forward function
        self.add = self.q.add

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

            return EscapedChar(self,
                               as_single_chars=SpecialPattern.restrict_special_chars)

        elif this_should_be_range and psm.char != "]":
            assert isinstance(self.q.ast, ast.CharClass)
            assert len(self.q.ast.elems) >= 1
            self.next_is_range = False
            t = ast.Range()
            t.begin = self.q.pop()
            t.end = ast.SingleChar()
            t.end.char = psm.char
            self.q.add(t)
            return self

        elif psm.char == "^":
            # if at the begining, it has a special meaning
            if this_is_empty:
                self.can_mutate = False
                self.q.ast.negate = True
            else:
                t = ast.SingleChar()
                t.char = psm.char
                self.q.add(t)
            return self

        elif psm.char == "]":
            if this_should_be_range:
                t = ast.SingleChar()
                t.char = "-"
                self.q.add(t)
            else:
                self.mutate_if_posix_like()

            self.prev.add(self.q.ast)
            return self.prev

        elif psm.char == "[":
            return CharClass(self)

        elif psm.char == "-" and len(self.q.ast.elems) >= 1:
            self.next_is_range = True
            return self

        else:
            t = ast.SingleChar()
            t.char = psm.char
            self.q.add(t)
            return self

    def mutate_if_posix_like(self):
        """
        Change from character class to pattern char if the content is matching
        POSIX-like classe.
        """
        assert isinstance(self.q.ast, ast.CharClass)

        # put in this variable everything that had happen but not saved into
        # the single char object
        # because mutation is only possible if the exact string of the content
        # match a pre-definied list, so if an unlogged char is consumed, it
        # must prevent mutation
        if not self.can_mutate:
            return

        if len(self.q.ast.elems) < SpecialPattern.min_len_posix_class + 2:
            return

        opening = self.q.ast.elems[0]
        if not isinstance(opening, ast.SingleChar) or opening.char != ":":
            return

        closing = self.q.ast.elems[-1]
        if not isinstance(closing, ast.SingleChar) or closing.char != ":":
            return

        is_only_ascii = lambda x: (isinstance(x, ast.SingleChar)
                                   and len(x.char) == 1
                                   and x.char.isalpha())
        class_may_be_a_word = not any(
            not is_only_ascii(x) for x in self.q.ast.elems[1:-1])
        if not class_may_be_a_word:
            return

        word = "".join(s.char for s in self.q.ast.elems[1:-1])
        if word not in SpecialPattern.posix_classes:
            return

        t = ast.PatternChar()
        t.pattern = word
        t.type = ast.PatternChar.Posix
        self.q.ast = t


#-------------------------------------
def parse(expr, **kw):
    sm = PSM()
    sm.source = Source(expr)
    sm.starts_with(OpeningOfGroup(parent=None, initial=True))
    sm.pre_action = kw.get("pre_action", None)
    sm.post_action = kw.get("post_action", None)
    sm.parse()
    return sm.state.g.group
