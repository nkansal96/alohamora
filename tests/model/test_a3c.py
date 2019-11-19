import random
from unittest import mock

from ray.rllib.agents.a3c import A3CAgent

from blaze.config.config import get_config
from blaze.environment import Environment
from blaze.model import a3c
from blaze.model.model import SavedModel
from tests.mocks.config import get_env_config, get_train_config


def get_episode_result():
    return {
        "episode_reward_mean": random.randint(0, 1000),
        "episode_reward_min": random.randint(0, 1000),
        "episode_reward_max": random.randint(0, 1000),
    }


def get_episode_result_dist(a, b):
    return {
        "episode_reward_mean": random.randint(a, b),
        "episode_reward_min": random.randint(a, b),
        "episode_reward_max": random.randint(a, b),
    }


class TestA3C:
    @mock.patch("ray.init")
    @mock.patch("ray.tune.run_experiments")
    def test_train_compiles(self, mock_run_experiments, _):
        a3c.train(get_train_config(), get_config(get_env_config()))
        mock_run_experiments.assert_called_once()

    def test_get_model(self):
        location = "/tmp/model_location"
        saved_model = a3c.get_model(location)
        assert isinstance(saved_model, SavedModel)
        assert saved_model.cls is A3CAgent
        assert saved_model.env is Environment
        assert saved_model.location == location


class TestStopCondition:
    def test_init(self):
        assert a3c.stop_condition()

    def test_call_bad_reward(self):
        sc = a3c.stop_condition()
        assert not sc(0, {})
        assert not sc(0, {"episode_reward_mean": 10})

    def test_stops_after_max_time(self):
        sc = a3c.stop_condition()
        assert not sc(0, {"episode_reward_mean": 1, "episode_reward_min": 0, "episode_reward_max": 2})
        assert sc(0, {"time_since_restore": a3c.MAX_TIME_SECONDS + 1})

    def test_call_records_episode_result(self):
        sc = a3c.stop_condition()
        assert not sc(0, {"episode_reward_mean": 1, "episode_reward_min": 0, "episode_reward_max": 2})
        assert list(sc.past_rewards) == [(0, 1, 2)]

        assert not sc(0, {"episode_reward_mean": 2, "episode_reward_min": 1, "episode_reward_max": 3})
        assert list(sc.past_rewards) == [(0, 1, 2), (1, 2, 3)]

    def test_window_size_remains_less_than_min_iters(self):
        sc = a3c.stop_condition()
        total_iters = a3c.WINDOW_SIZE * 2

        for _ in range(total_iters):
            assert not sc(0, get_episode_result())
            assert len(sc.past_rewards) <= a3c.WINDOW_SIZE

    def test_stops_after_max_iters(self):
        sc = a3c.stop_condition()
        total_iters = a3c.MAX_ITERATIONS

        for _ in range(total_iters):
            assert not sc(0, get_episode_result())
        assert sc(0, get_episode_result())

    def test_does_not_stop_before_min(self):
        sc = a3c.stop_condition()
        total_iters = a3c.MIN_ITERATIONS - 1

        for _ in range(total_iters):
            assert not sc(0, {"episode_reward_mean": 10, "episode_reward_min": 5, "episode_reward_max": 20})

    def test_stops_if_window_stddev_is_low(self):
        sc = a3c.stop_condition()
        total_iters = a3c.MIN_ITERATIONS * 2 + a3c.WINDOW_SIZE

        for i in range(total_iters):
            if not sc(0, get_episode_result_dist(min(i, a3c.MIN_ITERATIONS * 2), a3c.MIN_ITERATIONS * 2)):
                break
        else:
            assert False, "should have stopped earlier"
