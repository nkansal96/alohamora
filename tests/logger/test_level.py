from blaze.logger import Level


class TestLevel:
    def test_is_int(self):
        assert all(isinstance(val, Level) for val in list(Level))
        assert all(isinstance(val, int) for val in list(Level))

    def test_is_ordered(self):
        levels = [Level.VERBOSE, Level.DEBUG, Level.INFO, Level.WARN, Level.ERROR, Level.CRITICAL]
        assert levels == list(Level)

        for a, b in zip(levels[:-1], levels[1:]):
            assert a < b

    def test_str_representation(self):
        assert all(map(str, list(Level)))

    def test_has_distinct_color(self):
        colors = [l.color for l in list(Level)]
        assert len(colors) == len(set(colors))

    def test_has_distinct_context_key_color(self):
        colors = [l.context_key_color for l in list(Level)]
        assert len(colors) == len(set(colors))
