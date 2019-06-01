from blaze.config import client


class TestNetworkType:
    def test_has_int_type(self):
        for val in list(client.NetworkType):
            assert isinstance(val, int)


class TestNetworkSpeed:
    def test_has_int_type(self):
        for val in list(client.NetworkSpeed):
            assert isinstance(val, int)


class TestDeviceSpeed:
    def test_has_int_type(self):
        for val in list(client.DeviceSpeed):
            assert isinstance(val, int)


class TestNetworkToBandwidthRange:
    def test_all_combinations_covered(self):
        for network_type in list(client.NetworkType):
            for network_speed in list(client.NetworkSpeed):
                bw_low, bw_high = client.network_to_bandwidth_range(network_type, network_speed)
                assert bw_low < bw_high

    def test_all_slow_less_than_fast(self):
        for network_type in list(client.NetworkType):
            slow_bw_low, slow_bw_high = client.network_to_bandwidth_range(network_type, client.NetworkSpeed.SLOW)
            fast_bw_low, fast_bw_high = client.network_to_bandwidth_range(network_type, client.NetworkSpeed.FAST)
            assert slow_bw_low < fast_bw_low
            assert slow_bw_high < fast_bw_high


class TestNetworkToLatencyRange:
    def test_all_networks_covered(self):
        for network_type in list(client.NetworkType):
            latency_low, latency_high = client.network_to_latency_range(network_type)
            assert latency_low < latency_high


class TestDeviceSpeedToCpuSlowdown:
    def test_all_device_speeds_covered(self):
        for device_speed in list(client.DeviceSpeed):
            assert client.device_speed_to_cpu_slowdown(device_speed) > 0

    def test_faster_device_has_lower_cpu_slowdown(self):
        speeds = list(map(client.device_speed_to_cpu_slowdown, list(client.DeviceSpeed)))
        for a, b in zip(speeds[:-1], speeds[1:]):
            assert a < b


class TestClientEnvironment:
    def test_get_random_env(self):
        env = client.get_random_client_environment()
        assert isinstance(env, client.ClientEnvironment)
        assert isinstance(env.network_type, client.NetworkType)
        assert isinstance(env.network_speed, client.NetworkSpeed)
        assert isinstance(env.device_speed, client.DeviceSpeed)
        assert isinstance(env.bandwidth, int) and env.bandwidth > 0
        assert isinstance(env.latency, int) and env.latency > 0

    def test_get_fast_mobile_env(self):
        env = client.get_fast_mobile_client_environment()
        assert env.latency == 40
        assert env.bandwidth == 48000
        assert env.cpu_slowdown == 1

    def test_get_random_fast_lte_env(self):
        env = client.get_random_fast_lte_client_environment()
        assert isinstance(env, client.ClientEnvironment)
        assert env.network_type == client.NetworkType.LTE
        assert env.network_speed == client.NetworkSpeed.FAST
        assert env.device_speed in {client.DeviceSpeed.FAST_MOBILE, client.DeviceSpeed.SLOW_MOBILE}

        bandwidth_range = client.network_to_bandwidth_range(env.network_type, env.network_speed)
        latency_range = client.network_to_latency_range(env.network_type)

        assert latency_range[0] <= env.latency <= latency_range[1]
        assert bandwidth_range[0] <= env.bandwidth <= bandwidth_range[1]
        assert env.cpu_slowdown == client.device_speed_to_cpu_slowdown(env.device_speed)

    def test_generates_correct_range_for_network(self):
        for _ in range(100):
            env = client.get_random_client_environment()
            bw_low, bw_high = client.network_to_bandwidth_range(env.network_type, env.network_speed)
            latency_low, latency_high = client.network_to_latency_range(env.network_type)
            assert bw_low <= env.bandwidth <= bw_high
            assert latency_low <= env.latency <= latency_high

    def test_bandwidth_rand_is_multiple_of_100(self):
        for _ in range(10):
            env = client.get_random_client_environment()
            assert env.bandwidth % 100 == 0

    def test_latency_rand_is_even(self):
        for _ in range(10):
            env = client.get_random_client_environment()
            assert env.latency % 2 == 0
