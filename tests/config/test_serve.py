from blaze.config.serve import ServeConfig

class TestServeConfig():
  def test_compiles(self):
    c = ServeConfig(
      host="0.0.0.0",
      port=31000,
      max_workers=10,
    )
    assert isinstance(c, ServeConfig)
