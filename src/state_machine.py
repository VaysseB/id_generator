

class Source:
    """
    Source for parsing.
    """

    def __init__(self, content):
        self.pos = 0
        self.content = iter(content)
        self.curr = None
        self.done = False
        self.next()

    def next(self):
        try:
            self.curr = next(self.content)
            self.done = False
        except StopIteration:
            self.curr = None
            self.done = True
        return not self.done


class PSM:
    """
    Parser State Machine.
    """

    def __init__(self):
        self.source = None
        self.starting_state = None
        self.state = None
        self.error = None

        self.pre_action = None
        self.post_action = None

    def starts_with(self, s):
        self.starting_state = s
        self.state = s

    @property
    def can_end(self):
        return self.state is self.starting_state

    @property
    def char(self):
        return self.source.curr

    def parse_one(self):
        if self.pre_action:
            assert callable(self.pre_action)
            self.pre_action(self)

        next_state = self.state.next(self)

        if self.error:
            raise RuntimeError("parse error: " + self.error)

        assert next_state is not None, "internal error: cannot find next state"
        self.state = next_state
        self.source.next()

        if self.post_action:
            assert callable(self.post_action)
            self.post_action(self)

        # move the source and if at end, check if the state machine is in an
        # acceptable state (aka: back at start state)
        if self.source.done:
            if self.can_end:
                return False
            else:
                raise RuntimeError("parse error: unexpected end")

        return True

    def parse(self):
        while self.parse_one():
            pass


# >>> Examples for the state machine

class State:

    def __init__(self):
        self.data = {}
        self.transitions = ()

    def next(self, psm: PSM):
        return self.transitions[psm.char]

# <<< end of example
