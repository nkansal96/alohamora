import operator
from blaze.util.seq import ordered_uniq


class TestOrderedUniq:
    def test_preserves_order_of_unique_list(self):
        test = [5, 3, 1, 2, 4]
        assert ordered_uniq(test) == test

    def test_preserves_order_of_nonunique_list(self):
        test = [5, 3, 5, 1, 1, 2, 1, 4]
        actual = [5, 3, 1, 2, 4]
        assert ordered_uniq(test) == actual

    def test_uses_key_correctly(self):
        test = [("a", 5), ("b", 3), ("c", 5), ("d", 1), ("e", 1), ("f", 2), ("g", 1), ("h", 4)]
        actual = [("a", 5), ("b", 3), ("d", 1), ("f", 2), ("h", 4)]
        assert ordered_uniq(test, key=operator.itemgetter(1)) == actual

    def test_works_on_all_same_elems(self):
        test = [1, 1, 1, 1, 1]
        actual = [1]
        assert ordered_uniq(test) == actual

    def test_works_on_iterators(self):
        max_len = 10
        uniq_list = ordered_uniq(range(max_len))
        assert isinstance(uniq_list, list)
        assert len(uniq_list) == max_len
