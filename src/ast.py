
import builtins
_print = builtins.print


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
        # parts is a tuple of tuple
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
class Formatter:
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
        for line in self._format(ast, depth=0):
            _print(line)

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
        for (i, part) in enumerate(alt.parts):
            yield self._inline(depth+1, "#" + str(i))
            for elem in part:
                yield from self._format(elem, depth+2)

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
            yield self._raw("at least ", rpt.min, " times",
                       (", not greedy" if not rpt.greedy else ""))
        else:
            yield self._raw("between ", rpt.min, " and ", rpt.max,
                       (", not greedy" if not rpt.greedy else ""))


ast_format = Formatter()
def print(ast):
    ast_format.print(ast)


#-----------------------------------------------------------------------------
class Walker:
    def __init__(self):
        self.walkers = {
            Group       : self._walk_Group,
            MatchBegin  : self._walk_MatchBegin,
            MatchEnd    : self._walk_MatchEnd,
            Alternative : self._walk_Alternative,
            SingleChar  : self._walk_SingleChar,
            PatternChar : self._walk_PatternChar,
            Range       : self._walk_Range,
            CharClass   : self._walk_CharClass,
            NoneOrOnce  : self._walk_NoneOrOnce,
            NoneOrMore  : self._walk_NoneOrMore,
            OneTime     : self._walk_OneTime,
            OneOrMore   : self._walk_OneOrMore,
            Between     : self._walk_Between
        }

    def walk(self, ast, visitor, quantify: bool=True):
        if isinstance(ast, (list, tuple)):
            for item in ast:
                self.walkers[type(item)](item, visitor, quantify)
        else:
            self.walkers[type(ast)](ast, visitor, quantify)

    def _visit(self, type_name, ast, visitor, quantify: bool=True):
        method_name = "visit_" + type_name
        method = getattr(visitor, method_name, None)
        if callable(method):
            method(ast)

    def _walk_Group(self, group: Group, visitor, quantify: bool):
        self._visit("Group", group, visitor)
        if quantify:
            self.walk(group.quantifier, visitor)
        self.walk(group.seq, visitor)

    def _walk_MatchBegin(self, mb: MatchBegin, visitor, quantify: bool):
        self._visit("MatchBegin", mb, visitor)

    def _walk_MatchEnd(self, me: MatchEnd, visitor, quantify: bool):
        self._visit("MatchEnd", me, visitor)

    def _walk_Alternative(self, alt: Alternative, visitor, quantify: bool):
        self._visit("Alternative", alt, visitor)
        for part in alt.parts:
            self.walk(part, visitor)

    def _walk_SingleChar(self, sch: SingleChar, visitor, quantify: bool):
        self._visit("SingleChar", sch, visitor)
        if quantify:
            self.walk(sch.quantifier, visitor)

    def _walk_PatternChar(self, pch: PatternChar, visitor, quantify: bool):
        self._visit("PatternChar", pch, visitor)
        if quantify:
            self.walk(pch.quantifier, visitor)

    def _walk_Range(self, rng: Range, visitor, quantify: bool):
        self._visit("Range", rng, visitor)
        if quantify:
            self.walk(rng.quantifier, visitor)

    def _walk_CharClass(self, chcls: CharClass, visitor, quantify: bool):
        self._visit("CharClass", chcls, visitor)
        if quantify:
            self.walk(chcls.quantifier, visitor)
        self.walk(chcls.elems, visitor, False)

    def _walk_NoneOrOnce(self, q: NoneOrOnce, visitor, quantify: bool):
        self._visit("NoneOrOnce", q, visitor)

    def _walk_NoneOrMore(self, q: NoneOrMore, visitor, quantify: bool):
        self._visit("NoneOrMore", q, visitor)

    def _walk_OneTime(self, q: OneTime, visitor, quantify: bool):
        self._visit("OneTime", q, visitor)

    def _walk_OneOrMore(self, q: OneOrMore, visitor, quantify: bool):
        self._visit("OneOrMore", q, visitor)

    def _walk_Between(self, rpt: Between, visitor, quantify: bool):
        self._visit("Between", rp, visitor)


walker = Walker()
def visit(ast, visitor):
    walker.walk(ast, visitor)

