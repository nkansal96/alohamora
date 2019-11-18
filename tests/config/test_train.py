from blaze.config.train import TrainConfig


class TestTrainConfig:
    def test_compiles(self):
        c = TrainConfig(experiment_name="test", num_workers=16)
        assert isinstance(c, TrainConfig)
        assert c.resume == "prompt"

    def test_compiles_with_resume_bool(self):
        c = TrainConfig(experiment_name="test", num_workers=16, resume=True)
        assert isinstance(c, TrainConfig)
        assert c.resume
