
import string

import ast
from state_machine import PSM, Source




class SpecialPattern:
    individual_chars = ('t', 'n', 'v', 'f', 'r', '0')
    range_chars = ('d', 'D', 'w', 'W', 's', 'S')
    special_chars = ('^', '$', '[', ']', '(', ')', '{', '}', '\\', '.', '*',
                     '?', '+', '|')
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
    def __init__(self, group: OpeningOfGroup, initial: bool=False):
        self.group = group
        self.is_initial = initial
        self.prev = group if initial else self

    def add(self, other):
        self.group.add(other)

    def next(self, psm: PSM):

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
            g = EscapedChar(prev=self.prev)
            self.group.add_ast(g)
            return g

        elif psm.char == "[":
            r = CharClass(prev=self.prev)
            return r

# TODO insert here other cases

        else:
            c = ast.SingleChar()
            c.char = psm.char
            self.group.add(c)
            return self.prev


#--------------------------------------
class EscapedChar:

    def __init__(self, prev):
        self.prev = prev
        self.ast = ast.PatternChar()

    def next(self, psm: PSM):
        if psm.char in SpecialPattern.individual_chars \
           or psm.char in SpecialPattern.range_chars \
           or psm.char in SpecialPattern.special_chars:
            self.ast.pattern = psm.char
            return self.prev
        elif psm.char == "x":
            return AsciiChar(self)
        elif psm.char == "u":
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

    def next(self, psm: PSM):
        this_should_be_range = self.next_is_range
        self.next_is_range = False

        if this_should_be_range and psm.char != "]":
            self.next_is_range = False
            r = ast.Range()
            r.begin = self.ast.elems[-1]
            r.end = ast.SingleChar()
            r.end.char = psm.char
            self.swap_last(r)
            return self

        elif psm.char == "\\":
            s = EscapedChar(prev=self)
            self.add(s.ast)
            return s

        elif psm.char == "^":
            if not self.empty:
                psm.error = 'caret "^" must be escaped or at the begining'
            self.ast.negate = True
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


    @property
    def empty(self):
        return not self.ast.elems

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
        can_mutate = self.ast.negate is False
        if not can_mutate:
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
