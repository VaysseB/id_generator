

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
        self.quantifier = one_time


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
        self.quantifier = one_time


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
        self.quantifier = one_time


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
        self.quantifier = one_time


#-----------------------------------------------------------------------------
class NoneOrOnce:
    """
    Example: .?
    """
    pass

class NoneOrMore:
    """
    Example: .*
    """
    pass

class OneTime:
    """
    Example: .
    """
    pass

class OneOrMore:
    """
    Example: .+
    """
    pass

class Between:
    """
    Example: .{a,b}
    """
    def __init__(self):
        self.min = None
        self.max = None

none_or_once = NoneOrOnce()
none_or_more = NoneOrMore()
one_time = OneTime()
one_or_more = OneOrMore()
one_or_more_ungreedy = OneOrMore()


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
        return self._ident(depth) + "".join(str(x) for x in args)

    def _format_Group(self, group: Group, depth: int):
        name = (" \"" + group.name + "\"") if group.name is not None else ""
        if depth <= 0:
            yield self._inline(depth, "root", name)
        else:
            yield self._inline(depth, "group", name)
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
        yield self._inline(depth, "char: ", sch.char)

    def _format_PatternChar(self, pch: PatternChar, depth: int):
        if pch.type == PatternChar.Posix:
            yield self._inline(depth, "pattern: [posix] ", pch.pattern)
        elif pch.type == PatternChar.Unicode:
            yield self._inline(depth, "pattern: [unicode] ", pch.pattern)
        elif pch.type == PatternChar.Ascii:
            yield self._inline(depth, "pattern: [ascii] ", pch.pattern)
        else:
            yield self._inline(depth, "pattern: ", pch.pattern)

    def _format_Range(self, rng: Range, depth: int):
        yield self._inline(depth,
                           "range: ",
                           *self._format(rng.begin),
                           " to ",
                           *self._format(rng.end))

    def _format_CharClass(self, chcls: CharClass, depth: int):
        yield self._inline(depth, "class", " negated" * chcls.negate)
        for elem in chcls.elems:
            yield from self._format(elem, depth+1)

    def _format_NoneOrOnce(self, _: NoneOrOnce, depth: int):
        yield self._inline(depth, "0 or 1 time")

    def _format_NoneOrMore(self, _: NoneOrMore, depth: int):
        yield self._inline(depth, "0 or more")

    def _format_OneTime(self, _: OneTime, depth: int):
        yield self._inline(depth, "1 time")

    def _format_OneOrMore(self, _: OneOrMore, depth: int):
        yield self._inline(depth, "1 or more")

    def _format_Between(self, rpt: Between, depth: int):
        if rpt.min is None:
            yield self._inline(depth, "up to ", rpt.max, " times")
        elif rpt.max is None:
            yield self._inline(depth, "at least ", rpt.max, " times")
        else:
            yield self._inline(depth, "between ", rpt.min, " and ", rpt.max)


ast_format = AstFormatter()
def print(ast):
    ast_format.print(ast)
