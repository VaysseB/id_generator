
import ast
from state_machine import PSM, Source


#-------------------------------------
# Group

class Group:
    def __init__(self, initial=False, prev=None):
        self.is_initial = initial
        self.prev = prev
        self.ast = ast.Group()

    def next(self, psm: PSM):
        if not self.is_initial and psm.char == "?":
            return FirstOptionOfGroup(self)
        elif not self.is_initial and psm.char == ")":
            return self.prev
        elif psm.char == "(":
            g = Group(prev=self)
            self.ast.seq = self.ast.seq + (g.ast,)
            return g


class FirstOptionOfGroup:
    def __init__(self, group: Group):
        self.group = group

    def next(self, psm: PSM):
        if psm.char == ":":
            self.group.ast.ignored = True
            return ContentOfGroup(self.group)

        psm.error = 'expected ":", "<" or "="'


class ContentOfGroup:
    def __init__(self, group: Group):
        self.group = group

    def next(self, psm: PSM):
        if psm.char == ")":
            return self.group.prev
        assert False, "not implemented"



#--------------------------------------

def parse(expr, **kw):
    sm = PSM()
    sm.source = Source(expr)
    sm.starts_with(Group(initial=True))
    sm.pre_action = kw.get("pre_action", None)
    sm.post_action = kw.get("post_action", None)
    sm.parse()
    return sm.state.ast
