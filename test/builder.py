
import fix_import
import ast


class Expect:
    def __init__(self):
        self.ast = []

    def seq(self, *text):
        for c in text:
            s = ast.SingleChar()
            s.char = c
            self.ast.append(s)
        return self

    def chcls(self, *elems, **kw):
        s = ast.CharClass()
        if kw.get("dont_sequence", False):
            s.elems = tuple(elems)
        else:
            s.elems = tuple(Expect().seq(*elems).ast)
        s.__dict__.update(kw)
        self.ast.append(s)
        return self

    def raw_rng(self, begin, end):
        s = ast.Range()
        s.begin = ast.SingleChar()
        s.begin.char = begin
        s.end = ast.SingleChar()
        s.end.char = end
        self.ast.append(s)
        return self

    def chrng(self, begin, end, **kw):
        c = ast.CharClass()
        c.elems = (Expect().raw_rng(begin, end).ast[0],)
        c.__dict__.update(kw)
        self.ast.append(c)
        return self

    numrng = chrng

    def pattch(self, text, **kw):
        s = ast.PatternChar()
        s.pattern = text
        s.__dict__.update(kw)
        self.ast.append(s)
        return self

    def close_group(self, **kw):
        g = ast.Group()
        g.seq = tuple(self.ast)
        g.__dict__.update(kw)
        self.ast = [g]
        return self

    def bol(self):
        t = ast.MatchBegin()
        self.ast.append(t)
        return self

    def eol(self):
        t = ast.MatchEnd()
        self.ast.append(t)
        return self

    def raw_alt(self, *parts):
        t = ast.Alternative()
        t.elems = tuple(parts)
        self.ast.append(t)
        return self

    def q_maybe(self, greedy=True):
        q = ast.NoneOrOnce()
        q.greedy = greedy
        self.ast[-1].quantifier = q
        return self

    def q_0n(self, greedy=True):
        q = ast.NoneOrMore()
        q.greedy = greedy
        self.ast[-1].quantifier = q
        return self

    def q_1(self):
        self.ast[-1].quantifier = ast.OneTime()
        return self

    def q_1n(self, greedy=True):
        q = ast.OneOrMore()
        q.greedy = greedy
        self.ast[-1].quantifier = q
        return self

    def q_rng(self, min_, max_, greedy=True):
        r = ast.Between()
        r.min = min_
        r.max = max_
        r.greedy = greedy
        self.ast[-1].quantifier = r
        return self


    def build(self, **kw):
        root = ast.Group()
        root.seq = tuple(self.ast)
        root.__dict__.update(kw)
        return root

