
import ast
from state_machine import PSM, Source



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

        assert False, "not implemented: {}".format(psm.char)


#--------------------------------------
class EscapedChar:
    individual_chars = ('t', 'n', 'v', 'f', 'r', '0')
    range_chars = ('d', 'D', 'w', 'W', 's', 'S')
    special_chars = ('^', '$', '[', ']', '(', ')', '{', '}', '\\', '.', '*',
                     '?', '+', '|')

    def __init__(self, prev):
        self.prev = prev
        self.ast = ast.PatternChar()

    def next(self, psm: PSM):
        if psm.char in EscapedChar.individual_chars \
           or psm.char in EscapedChar.range_chars \
           or psm.char in EscapedChar.special_chars:
            self.ast.pattern = psm.char
            return self.prev
        # TODO \xhh and \uhhh
        else:
            psm.error = "unauthorized escape of {}".format(psm.char)


#--------------------------------------

def parse(expr, **kw):
    sm = PSM()
    sm.source = Source(expr)
    sm.starts_with(OpeningOfGroup(initial=True))
    sm.pre_action = kw.get("pre_action", None)
    sm.post_action = kw.get("post_action", None)
    sm.parse()
    return sm.state.ast
