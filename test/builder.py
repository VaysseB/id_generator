
import fix_import
import parser


class Expect:
    def __init__(self):
        self.ast = []

    def seq(self, *text):
        for c in text:
            s = parser.SingleChar()
            s.char = c
            self.ast.append(s)
        return self

    def chcls(self, *elems, **kw):
        s = parser.CharClass()
        s.elems = tuple(iter(elems))
        s.__dict__.update(kw)
        self.ast.append(s)
        return self

    def raw_rng(self, begin, end):
        s = parser.Range()
        s.begin = begin
        s.end = end
        self.ast = [s]
        return self

    def chrng(self, begin, end, **kw):
        s = parser.Range()
        s.begin = begin
        s.end = end

        c = parser.CharClass()
        c.elems = (s,)
        c.__dict__.update(kw)

        self.ast.append(c)
        return self

    def numrng(self, begin, end, **kw):
        s = parser.Range()
        s.begin = begin
        s.end = end

        c = parser.CharClass()
        c.elems = (s,)
        c.__dict__.update(kw)

        self.ast.append(c)
        return self

    def pattch(self, text, **kw):
        s = parser.PatternChar()
        s.pattern = text
        s.__dict__.update(kw)
        self.ast.append(s)
        return self

    def close_group(self, **kw):
        g = parser.Group()
        g.seq = tuple(self.ast)
        g.__dict__.update(kw)
        self.ast = [g]
        return self

    def bol(self):
        t = parser.MatchBegin()
        self.ast.append(t)
        return self

    def eol(self):
        t = parser.MatchEnd()
        self.ast.append(t)
        return self

    def alt(self, *parts):
        t = parser.Alternative()
        t.elems = tuple(parts)
        self.ast.append(t)
        return self

    def q_maybe(self):
        self.ast[-1].quantifier = parser.none_or_once
        return self

    def q_0n(self):
        self.ast[-1].quantifier = parser.none_or_more
        return self

    def q_1(self):
        self.ast[-1].quantifier = parser.one_time
        return self

    def q_1n(self, greedy=True):
        if greedy:
            self.ast[-1].quantifier = parser.one_or_more
        else:
            self.ast[-1].quantifier = parser.one_or_more_ungreedy
        return self

    def q_rng(self, min_, max_):
        r = parser.Between()
        r.min = min_
        r.max = max_
        self.ast[-1].quantifier = r
        return self


    def build(self, **kw):
        root = parser.Group()
        root.seq = tuple(self.ast)
        root.__dict__.update(kw)
        return root

