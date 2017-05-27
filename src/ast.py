

class Group:
    """
    Example: (...), (?:...), (?=...), (?!...), (?<...>...)
    """

    PositiveLookhead = 1
    NegativeLookhead = -1

    def __init__(self):
        self.seq = ()
        self.ignored = False
        self.name = None
        self.lookhead = None
        self.quantifier = OneTime()


class MatchBegin:
    """
    Example: ^
    """
    pass


class MatchEnd:
    """
    Example: $
    """
    pass


class Alternative:
    """
    Example: .|.
    This class cannot be quantified. Only the group it is included in can.
    """

    def __init__(self):
        self.parts = ()


class SingleChar:
    """
    Example: any character
    """

    def __init__(self):
        self.char = None
        self.quantifier = OneTime()


class PatternChar:
    Ascii = 1
    Unicode = 2
    Posix = 3

    r"""
    Single: \t, \n, \v, \f, \r, \0,
    Any: \d, \D, \s, \S, \w, \W
    Special: \xhh \uhhh,
    Escaped: ^, $, \, ., +, ?, (, ), [, ], {, }, |
    POSIX: alnum, alpha, blank, cntrl, digit, graph, lower, print, punc, space,
    upper, xdigit, d, w, s
    """

    def __init__(self):
        self.pattern = ""
        self.type = None
        self.quantifier = OneTime()


class Range:
    """
    Example: [a-b]
    This class must be inside the CharClass, it cannot be used as standalone.
    """

    def __init__(self):
        self.begin = None
        self.end = None


class CharClass:
    """
    Example: [a], [^a]
    """

    def __init__(self):
        self.elems = ()
        self.negate = False
        self.quantifier = OneTime()


#-----------------------------------------------------------------------------
class NoneOrOnce:
    """
    Example: .?
    """
    def __init__(self):
        self.greedy = True

class NoneOrMore:
    """
    Example: .*
    """
    def __init__(self):
        self.greedy = True

class OneTime:
    """
    Example: .
    """
    pass

class OneOrMore:
    """
    Example: .+
    """
    def __init__(self):
        self.greedy = True

class Between:
    """
    Example: .{a,b}
    """
    def __init__(self):
        self.min = None
        self.max = None
        self.greedy = True

#-----------------------------------------------------------------------------
class AstFormatter:
    def __init__(self):
        self.formatters = {
            Group       : self._format_Group,
            MatchBegin  : self._format_MatchBegin,
            MatchEnd    : self._format_MatchEnd,
            Alternative : self._format_Alternative,
            SingleChar  : self._format_SingleChar,
            PatternChar : self._format_PatternChar,
            Range       : self._format_Range,
            CharClass   : self._format_CharClass,
            NoneOrOnce  : self._format_NoneOrOnce,
            NoneOrMore  : self._format_NoneOrMore,
            OneTime     : self._format_OneTime,
            OneOrMore   : self._format_OneOrMore,
            Between     : self._format_Between
        }

    def print(self, ast):
        import builtins
        for line in self._format(ast, depth=0):
            builtins.print(line)

    def _format(self, ast, depth=0):
        yield from self.formatters[type(ast)](ast, depth)

    def _ident(self, depth):
        if depth <= 0:
            return ""
        elif depth <= 1:
            return "|-- "
        else:
            return "|  " * (depth - 1) + "|-- "

    def _inline(self, depth, *args):
        return self._ident(depth) + self._raw(*args)

    def _raw(self, *args):
        return "".join(str(x) for x in args)

    def _format_quantifier(self, quantifier):
        if quantifier:
            text = "".join(self._format(quantifier))
            return ("  [" + text + "]") if text else ""
        return ""

    def _format_Group(self, group: Group, depth: int):
        name = (" \"" + group.name + "\"") if group.name is not None else ""
        ignored = " (ignored)" if group.ignored else ""
        lookhead = ("" if group.lookhead is None else
                   (" lookhead:" + (
                       "pos"
                       if group.lookhead == Group.PositiveLookhead
                       else "neg"
                   )))
        if depth <= 0:
            yield self._inline(depth, "root", name, ignored, lookhead,
                               self._format_quantifier(group.quantifier))
        else:
            yield self._inline(depth, "group", name, ignored, lookhead,
                               self._format_quantifier(group.quantifier))
        for elem in group.seq:
            yield from self._format(elem, depth+1)

    def _format_MatchBegin(self, _: MatchBegin, depth: int):
        yield self._inline(depth, "^begin")

    def _format_MatchEnd(self, _: MatchEnd, depth: int):
        yield self._inline(depth, "end$")

    def _format_Alternative(self, alt: Alternative,  depth: int):
        yield self._inline(depth, "alt")
        for elem in alt.parts:
            yield from self._format(elem, depth+1)

    def _format_SingleChar(self, sch: SingleChar, depth: int):
        yield self._inline(depth, "char: ", sch.char,
                               self._format_quantifier(sch.quantifier))

    def _format_PatternChar(self, pch: PatternChar, depth: int):
        if pch.type == PatternChar.Posix:
            yield self._inline(depth, "pattern: [posix] ", pch.pattern,
                               self._format_quantifier(pch.quantifier))
        elif pch.type == PatternChar.Unicode:
            yield self._inline(depth, "pattern: [unicode] ", pch.pattern,
                               self._format_quantifier(pch.quantifier))
        elif pch.type == PatternChar.Ascii:
            yield self._inline(depth, "pattern: [ascii] ", pch.pattern,
                               self._format_quantifier(pch.quantifier))
        else:
            yield self._inline(depth, "pattern: ", pch.pattern,
                               self._format_quantifier(pch.quantifier))

    def _format_Range(self, rng: Range, depth: int):
        yield self._inline(depth,
                           "range: ",
                           *self._format(rng.begin),
                           " to ",
                           *self._format(rng.end))

    def _format_CharClass(self, chcls: CharClass, depth: int):
        yield self._inline(depth, "class", " negated" * chcls.negate,
                               self._format_quantifier(chcls.quantifier))
        for elem in chcls.elems:
            yield from self._format(elem, depth+1)

    def _format_NoneOrOnce(self, q: NoneOrOnce, depth: int):
        yield self._raw("0 or 1 time",
                       (", not greedy" if not q.greedy else ""))

    def _format_NoneOrMore(self, q: NoneOrMore, depth: int):
        yield self._raw("0 or more",
                       (", not greedy" if not q.greedy else ""))

    def _format_OneTime(self, _: OneTime, depth: int):
        yield ""

    def _format_OneOrMore(self, q: OneOrMore, depth: int):
        yield self._raw("1 or more",
                       (", not greedy" if not q.greedy else ""))

    def _format_Between(self, rpt: Between, depth: int):
        if rpt.min is None:
            yield self._raw("up to ", rpt.max, " times",
                       (", not greedy" if not rpt.greedy else ""))
        elif rpt.max is None:
            yield self._raw("at least ", rpt.max, " times",
                       (", not greedy" if not rpt.greedy else ""))
        else:
            yield self._raw("between ", rpt.min, " and ", rpt.max,
                       (", not greedy" if not rpt.greedy else ""))


ast_format = AstFormatter()
def print(ast):
    ast_format.print(ast)
