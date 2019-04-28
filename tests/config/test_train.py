from blaze.config.train import TrainConfig

class TestTrainConfig():
  def test_compiles(self):
    c = TrainConfig(
      experiment_name="test",
      model_dir="/tmp/test",
      num_cpus=16,
      max_timesteps=10,
    )
    assert isinstance(c, TrainConfig)
    assert c.resume == "prompt"

  def test_compiles_with_resume_bool(self):
    c = TrainConfig(
      experiment_name="test",
      model_dir="/tmp/test",
      num_cpus=16,
      max_timesteps=10,
      resume=True
    )
    assert isinstance(c, TrainConfig)
    assert c.resume
