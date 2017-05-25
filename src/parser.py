

class Group:
    """
    Example: (...), (?:...), (?=...), (?!...), (?<...>...)
    """

    PositiveLookhead = 1
    NegativeLookhead = -1

    def __init__(self):
        self.seq = ()
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
def parse(expr):
    pass

