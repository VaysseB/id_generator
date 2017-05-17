
import argparse
import random
import functools


LOG_DEBUG = False

class FixGenerator:
    def __init__(self, content):
        self.content = content
        self.count = 1

    def __iter__(self):
        return self

    def __next__(self):
        return self.content


class RangeGenerator:
    def __init__(self, start, end, fixed_length):
        assert start <= end
        self.start = start
        self.end = end
        self.fixed_length = int(fixed_length) if fixed_length else 0
        self.count = self.end - self.start + 1

    def __iter__(self):
        return self

    def __next__(self):
        value = str(random.randint(self.start, self.end))
        if self.fixed_length:
            value = value.zfill(self.fixed_length)
        return value


class IdentifierGenerator:
    def __init__(self, fields, limit):
        self.fields = tuple(iter(f) for f in fields)
        combinatory_limit = functools.reduce(lambda x,y: x*y, (f.count for f in fields), 1)
        self.limit = min(limit, combinatory_limit)
        self.produced = set()

    def __iter__(self):
        return self

    def __next__(self):
        if self.limit <= 0:
            raise StopIteration()

        newest = self._generate()
        while newest in self.produced:
            newest = self._generate()

        self.limit -= 1
        self.produced.add(newest)
        return newest

    def _generate(self):
        return "".join(next(f) for f in self.fields)


def parse_pattern(raw_sequence):

    class TextParser:
        def __init__(self):
            self.text = []

        def parse(self, source):
            if source.consume_escaping():
                self.text.append(source.curr)
            elif source.curr == "[":
                return FieldParser()
            elif source.curr == "]":
                source.parse_error("unescaped \"]\"")
            elif source.curr == "\\":
                source.enable_escaping()
            else:
                self.text.append(source.curr)
            return self

        def build(self):
            text = "".join(self.text)
            return FixGenerator(text)

        def __str__(self):
            return "text|{}".format("".join(self.text))


    class FieldParser:
        def __init__(self):
            self.range_start = []
            self.range_end = []
            self.option = {}
            self._parser_state = self._parse_start

        def __str__(self):
            return "range|{}/{}/{}{}".format(
                    "".join(self.range_start),
                    "".join(self.range_end),
                    "".join(self.option.get("pad_len", [])),
                    "".join("z" if self.option.get("pad_field", False) else "")
                    )

        def put_error_if_left(self, source):
            source.error_if_done = "unfinished field declaration"

        def _parse_start(self, source):
            if source.curr.isnumeric():
                self.range_start.append(source.curr)
            elif source.curr == "-":
                if not self.range_start:
                    source.parse_error("unspecified start of field")
                else:
                    self._parser_state = self._parse_end
                    self.put_error_if_left(source)
            else:
                source.parse_error("expect number or \"-\", got \"{}\"".format(source.curr))
            return self

        def _parse_end(self, source):
            if source.curr.isnumeric():
                self.range_end.append(source.curr)
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

        def _parse_start_of_option(self, source):
            if source.curr.isnumeric():
                if "pad_len" in self.option:
                    source.parse_error("duplication of padding lenght in field option")
                else:
                    self.option["pad_len"] = [source.curr]
                self.some_options = True
                self._parser_state = self._parse_option_pad_len
            elif source.curr == "z":
                if "pad_field" in self.option:
                    source.parse_error("duplication of '{}' in field option".format(source.curr))
                else:
                    self.option["pad_field"] = True
                self.some_options = True
                self._parser_state = self._parse_closing
            else:
                source.parse_error("expect number or \"z\"")
            return self

        def _parse_option_pad_len(self, source):
            if source.curr.isnumeric():
                assert "pad_len" in self.option, "internal error (impossible situation)"
                self.option["pad_len"].append(source.curr)
            elif source.curr == "z":
                if "pad_field" in self.option:
                    source.parse_error("duplication of '{}' in field option".format(source.curr))
                else:
                    self.option["pad_field"] = True
                self.some_options = True
                self._parser_state = self._parse_closing
            else:
                source.parse_error("expect number or \"z\"")
            return self

        def _parse_closing(self, source):
            if source.curr == "]":
                return None
            else:
                source.parse_error("expect \"]\"")
            return self

        def parse(self, source):
            return self._parser_state(source)

        def build(self):
            start = int("".join(self.range_start))
            end = int("".join(self.range_end))
            pad_len = None
            if self.option.get("pad_field", False):
                if "pad_len" in self.option:
                    pad_len = int("".join(self.option["pad_len"]))
                else:
                    pad_len = len(str(end))
            return RangeGenerator(start, end, pad_len)


    def find_parser(source):
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


    class PatternReader:
        def __init__(self, pattern):
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
            if LOG_DEBUG: print("Start[{}]".format(self.curr), field)

            self._next()

            # parsing loop
            while self.curr:
                if field is None:
                    if LOG_DEBUG: print("Search[{}]".format(self.curr))
                    field = find_parser(self)
                    if LOG_DEBUG: print("Found[{}]".format(self.curr), field)
                    self.raise_error_if_any()
                    assert field is not None, "internal error (cannot parse '{}')".format(self.curr)

                    # clear error on unclosed field because the last one did end on purpose
                    self.error_if_done = None

                    self._next()
                    continue

                if self.fields[-1] != field:
                    self.fields.append(field)

                field = field.parse(self)
                if LOG_DEBUG: print("Loop[{}]".format(self.curr), field)
                self.raise_error_if_any()
                self._next()

            if field is not None and self.error_if_done:
                self.error = self.error_if_done
                self.raise_error_if_any()

        def raise_error_if_any(self):
            if self.error:
                if LOG_DEBUG: print("Parsing error:", self.error)
                exit(1)

        def build(self):
            assert self.error is None, "internal error (cannot build if error is set)"
            return tuple(f.build() for f in self.fields)

    #
    parser = PatternReader(raw_sequence)
    return parser.parse_and_build()


def parse_args():
    parser = argparse.ArgumentParser(
            description="Generator of identifier"
            )
    parser.add_argument("-c", "--count", type=int, help="Number of identifier generated")
    parser.add_argument("pattern", type=str, help="Identifier format")
    return parser.parse_args()


if __name__ == "__main__":
    import os
    LOG_DEBUG = bool(os.getenv("LOG_DEBUG", LOG_DEBUG))

    args = parse_args()
    fields = parse_pattern(args.pattern)
    limit = int(args.count if args.count else 20)
    for id_ in IdentifierGenerator(fields, limit):
        print(id_)
