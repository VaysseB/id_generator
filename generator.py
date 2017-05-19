
import random
import functools


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
        self.start = int(start)
        self.end = int(end)
        assert self.start <= self.end
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
