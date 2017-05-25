

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
        self.posix = False
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
class Printer:
    def __init__(self):
        self.printers = {
            Group       : self._print_Group,
            MatchBegin  : self._print_MatchBegin,
            MatchEnd    : self._print_MatchEnd,
            Alternative : self._print_Alternative,
            SingleChar  : self._print_SingleChar,
            PatternChar : self._print_PatternChar,
            Range       : self._print_Range,
            CharClass   : self._print_CharClass,
            NoneOrOnce  : self._print_NoneOrOnce,
            NoneOrMore  : self._print_NoneOrMore,
            OneTime     : self._print_OneTime,
            OneOrMore   : self._print_OneOrMore,
            Between     : self._print_Between
        }

    def print(self, ast, depth=0):
        self.printers[type(ast)](ast, depth)

    def _ident(self, depth):
        if depth <= 0:
            return ""
        elif depth <= 1:
            return "|-- "
        else:
            return "|  " * (depth - 1) + "|-- "

    def _print(self, depth, *args):
        import builtins
        builtins.print(self._ident(depth), *args, sep="")

    def _print_Group(self, group: Group, depth: int):
        name = (" \"" + group.name + "\"") if group.name is not None else ""
        if depth <= 0:
            self._print(depth, "root", name)
        else:
            self._print(depth, "group", name)
        for elem in group.seq:
            self.print(elem, depth+1)

    def _print_MatchBegin(self, _: MatchBegin, depth: int):
        self._print(depth, "^begin")

    def _print_MatchEnd(self, _: MatchEnd, depth: int):
        self._print(depth, "end$")

    def _print_Alternative(self, alt: Alternative,  depth: int):
        self._print(depth, "alt")
        for elem in alt.parts:
            self.print(elem, depth+1)

    def _print_SingleChar(self, sch: SingleChar, depth: int):
        self._print(depth, "char: ", sch.char)

    def _print_PatternChar(self, pch: PatternChar, depth: int):
        if pch.posix:
            self._print(depth, "pattern: [:", pch.pattern, ":]")
        else:
            self._print(depth, "pattern: ", pch.pattern)

    def _print_Range(self, rng: Range, depth: int):
        self._print(depth, "range: ", rng.begin, " to ", rng.end)

    def _print_CharClass(self, chcls: CharClass, depth: int):
        self._print(depth, "class", " negated" * chcls.negate)
        for elem in chcls.elems:
            self.print(elem, depth+1)

    def _print_NoneOrOnce(self, _: NoneOrOnce, depth: int):
        self._print(depth, "0 or 1 time")

    def _print_NoneOrMore(self, _: NoneOrMore, depth: int):
        self._print(depth, "0 or more")

    def _print_OneTime(self, _: OneTime, depth: int):
        self._print(depth, "1 time")

    def _print_OneOrMore(self, _: OneOrMore, depth: int):
        self._print(depth, "1 or more")

    def _print_Between(self, rpt: Between, depth: int):
        if rpt.min is None:
            self._print(depth, "up to ", rpt.max, " times")
        elif rpt.max is None:
            self._print(depth, "at least ", rpt.max, " times")
        else:
            self._print(depth, "between ", rpt.min, " and ", rpt.max)


printer = Printer()
def print(ast):
    printer.print(ast)
