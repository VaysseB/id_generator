
import logging

import generator


class ExtractSeq:
    """Temporary storage for extracted content from the source."""

    def __init__(self):
        self._seq = []

    def add(self, c: str):
        self._seq.append(c)

    def str(self) -> str:
        return "".join(self._seq)

    def int(self, w=10) -> int:
        return int(self.str(), w)

    def __str__(self):
        return self.str()


class Source:
    """Reader of expression."""

    def __init__(self, pattern):
        self.log = logging.getLogger("source.parser")
        self.pattern = iter(pattern)
        self.curr = None
        self.escaping = None
        self.fields = []
        self.error = None
        self.error_if_done = None

    def parse_and_build(self):
        self.parse()
        return self.build()

    def consume_escaping(self):
        if self.escaping:
            self.escaping = False
            return True
        return False

    def enable_escaping(self):
        assert not self.escaping, "internal error (cannot set escaping twice)"
        self.escaping = True

    def parse_error(self, msg):
        assert self.error is None, "internal error (a second parsing error was set without the first be consumed)"
        self.error = msg

    def _next(self):
        self.curr = next(self.pattern, None)

    def parse(self):
        # init parsing
        self._next()
        if self.curr is None:
            return

        field = find_parser(self)
        if field is None:
            self.raise_error_if_any()
            return
        self.fields.append(field)
        self.log.debug("Start[{}]{}".format(self.curr, field))

        self._next()

        # parsing loop
        while self.curr:
            if field is None:
                self.log.debug("Search[{}]".format(self.curr))
                field = find_parser(self)
                self.log.debug("Found[{}]{}".format(self.curr, field))
                self.raise_error_if_any()
                assert field is not None, "internal error (cannot parse '{}')".format(self.curr)

                # clear error on unclosed field because the last one did end on purpose
                self.error_if_done = None

                self._next()
                continue

            if self.fields[-1] != field:
                self.fields.append(field)

            field = field.parse(self)
            self.log.debug("Loop[{}]{}".format(self.curr, field))
            self.raise_error_if_any()
            self._next()

        if field is not None and self.error_if_done:
            self.error = self.error_if_done
            self.raise_error_if_any()

    def raise_error_if_any(self):
        if self.error:
            self.log.debug("Parsing error: {}".format(self.error))
            exit(1)

    def build(self):
        assert self.error is None, "internal error (cannot build if error is set)"
        return tuple(f.build() for f in self.fields)


class TextParser:
    """Parser for raw text sequence."""

    def __init__(self):
        self.text = ExtractSeq()

    def parse(self, source: Source):
        """Parse the current character returns the next parser."""
        if source.consume_escaping():
            self.text.add(source.curr)
        elif source.curr == "[":
            return FieldParser()
        elif source.curr == "]":
            source.parse_error("unescaped \"]\"")
        elif source.curr == "\\":
            source.enable_escaping()
        else:
            self.text.add(source.curr)
        return self

    def build(self):
        return generator.FixGenerator(self.text.str())

    def __str__(self):
        return "text|{}".format(self.text)


class FieldParser:
    """Parser for field (like number range)."""

    def __init__(self):
        self.range_start = ExtractSeq()
        self.range_end = ExtractSeq()
        self.option = {}
        self._parser_state = self._parse_start

    def __str__(self):
        return "range|{}/{}/{}{}".format(
                self.range_start,
                self.range_end,
                self.option.get("pad_len", ""),
                ("z" if self.option.get("pad_field", False) else "")
                )

    def put_error_if_left(self, source: Source):
        source.error_if_done = "unfinished field declaration"

    def _parse_start(self, source: Source):
        if source.curr.isnumeric():
            self.range_start.add(source.curr)
        elif source.curr == "-":
            if not self.range_start:
                source.parse_error("unspecified start of field")
            else:
                self._parser_state = self._parse_end
                self.put_error_if_left(source)
        else:
            source.parse_error("expect number or \"-\", got \"{}\"".format(source.curr))
        return self

    def _parse_end(self, source: Source):
        if source.curr.isnumeric():
            self.range_end.add(source.curr)
        elif source.curr == "|":
            if not self.range_end:
                source.parse_error("unspecified end of field")
            else:
                self._parser_state = self._parse_start_of_option
                self.put_error_if_left(source)
        elif source.curr == "]":
            if not self.range_end:
                source.parse_error("unspecified end of field")
            else:
                return None
        else:
            source.parse_error("expect number or \"|\" or \"]\", got \"{}\"".format(source.curr))
        return self

    def _parse_start_of_option(self, source: Source):
        if source.curr.isnumeric():
            if "pad_len" in self.option:
                lenght = self.option["pad_lenght"]
            else:
                pad_len = ExtractSeq()
                self.option["pad_len"] = pad_len
            pad_len.add(source.curr)
            self.some_options = True
        elif source.curr == "z":
            if "pad_field" in self.option:
                source.parse_error("duplication of '{}' in field option".format(source.curr))
            else:
                self.option["pad_field"] = True
            self.some_options = True
            self._parser_state = self._parse_closing
        elif source.curr == "]":
            return None
        else:
            source.parse_error("expect number or \"z\"")
        return self

    def _parse_closing(self, source: Source):
        if source.curr == "]":
            return None
        else:
            source.parse_error("expect \"]\"")
        return self

    def parse(self, source: Source):
        """Parse the current character returns the next parser."""
        return self._parser_state(source)

    def build(self):
        start = self.range_start.int()
        end = self.range_end.int()
        pad_len = None
        if self.option.get("pad_field", False):
            if "pad_len" in self.option:
                pad_len = self.option["pad_len"].int()
            else:
                pad_len = len(str(end))
        return generator.RangeGenerator(start, end, pad_len)


def find_parser(source: Source):
    """Find the parser from the current character."""
    if source.consume_escaping():
        assert False, "internal error (impossible situation)"
    elif source.curr == "\\":
        source.enable_escaping()
        return TextParser()
    elif source.curr == "[":
        f = FieldParser()
        f.put_error_if_left(source)
        return f
    elif source.curr == "]":
        source.parse_error("unescaped \"]\"")
    else:
        p = TextParser()
        return p.parse(source)

