
import fix_import
import ast


def _make_quantifier(q):
    if q == 1 or q == "1":
        return ast.OneTime()

    qt = None
    ungreedy = q.endswith("?") and len(q) >= 2
    q = q[:-1] if ungreedy else q

    if q == "?":
        qt = ast.NoneOrOnce()
    elif q == "*":
        qt = ast.NoneOrMore()
    elif q == "+":
        qt = ast.OneOrMore()
    else:
        min_, max_ = q.split(",")
        qt = ast.Between()
        qt.min = int(min_) if min_ else None
        qt.max = int(max_) if max_ else None

    qt.greedy = not ungreedy
    return qt


def ch(c: str, quant=1) -> ast.SingleChar:
    assert isinstance(c, str), "character of SingleChar must be str"
    t = ast.SingleChar()
    t.char = c
    t.quantifier = _make_quantifier(quant)
    return t


def class_(*items, reverse=False, quant=1) -> ast.CharClass:
    for item in items:
        error = ("item of CharClass must be SingleChar or PatternChar or Range, not "
                    + type(item).__qualname__)
        assert isinstance(item, (ast.SingleChar, ast.PatternChar, ast.Range)), error

    t = ast.CharClass()
    t.elems = tuple(items)
    t.quantifier = _make_quantifier(quant)
    t.negate = reverse
    return t


def rang(begin, end) -> ast.Range:
    assert isinstance(begin, (ast.SingleChar, ast.PatternChar)), \
                "begin of Range must be SingleChar or PatternChar"
    assert isinstance(end, (ast.SingleChar, ast.PatternChar)), \
                "end of Range must be SingleChar or PatternChar"

    t = ast.Range()
    t.begin = begin
    t.end = end
    return t


def rang_ch(begin, end) -> ast.Range:
    sb = ast.SingleChar()
    sb.char = begin
    se = ast.SingleChar()
    se.char = end
    return rang(sb, se)


def ptrn(c: str, type=None, quant=1) -> ast.PatternChar:
    assert isinstance(c, str), "character of PatternChar must be str"
    t = ast.PatternChar()
    t.pattern = c
    t.quantifier = _make_quantifier(quant)
    if type is not None:
        t.type = type
    return t


def grp(*items, name=None, ign=None, lkhead=None, quant=1) -> ast.Group:
    t = ast.Group()
    t.seq = tuple(items)
    t.quantifier = _make_quantifier(quant)
    t.ignored = t.ignored if ign is None else ign
    t.name = t.name if name is None else name
    t.lookhead = t.lookhead if lkhead is None else lkhead
    return t


def bol() -> ast.MatchBegin:
    return ast.MatchBegin()


def eol() -> ast.MatchEnd:
    return ast.MatchEnd()


def alt(*items) -> ast.Alternative:
    t = ast.Alternative()
    t.elems = tuple(items)
    return t

