
import ast
from state_machine import PSM, Source


def find_next(psm: PSM, prev):
    if psm.char == "(":
        g = OpeningOfGroup(prev=prev)
        return g

    assert False, "not implemented: {}".format(psm.char)



#-------------------------------------
# Group

class OpeningOfGroup:
    def __init__(self, initial=False, prev=None):
        self.is_initial = initial
        self.prev = prev
        self.ast = ast.Group()

    def next(self, psm: PSM):
        if not self.is_initial and psm.char == "?":
            return FirstOptionOfGroup(self)
        elif not self.is_initial and psm.char == ")":
            return self.prev

        state = find_next(psm, self)
        self.add_ast(state)
        return state

    def add_ast(self, other):
        self.ast.seq = self.ast.seq + (other.ast,)


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
    def __init__(self, group: OpeningOfGroup):
        self.group = group

    def next(self, psm: PSM):
        if psm.char == ")":
            return self.group.prev

        state = find_next(psm, self)
        self.group.add_ast(state)
        return state



#--------------------------------------

def parse(expr, **kw):
    sm = PSM()
    sm.source = Source(expr)
    sm.starts_with(OpeningOfGroup(initial=True))
    sm.pre_action = kw.get("pre_action", None)
    sm.post_action = kw.get("post_action", None)
    sm.parse()
    return sm.state.ast
