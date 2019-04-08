from blaze.evaluator.result import Result

class TestResult():
  def test_result_uses_speed_index(self):
    r = Result(speedIndex=100)
    assert r.speed_index == 100
    r = Result(**{'speedIndex': 100})
    assert r.speed_index == 100

  def test_result_uses_default_speed_index_if_not_specified(self):
    r = Result()
    assert r.speed_index == 0

  def test_result_ignores_other_args(self):
    r = Result(random_key=10)
    assert r.speed_index == 0
    r = Result(speedIndex=100, random_key=10)
    assert r.speed_index == 100

  def test_repr(self):
    r = repr(Result(speedIndex=1000))
    assert "Result" in r
    assert "speed_index" in r
    assert str(1000) in r
