from blaze.config import client

class TestNetworkType():
  def test_has_int_type(self):
    for val in list(client.NetworkType):
      assert isinstance(val, int)

class TestNetworkBandwidth():
  def test_has_int_type(self):
    for val in list(client.NetworkBandwidth):
      assert isinstance(val, int)

class TestNetworkLatency():
  def test_has_int_type(self):
    for val in list(client.NetworkLatency):
      assert isinstance(val, int)

class TestDeviceSpeed():
  def test_has_int_type(self):
    for val in list(client.DeviceSpeed):
      assert isinstance(val, int)

class TestClientEnvironment():
  def test_get_random_env(self):
    env = client.get_random_client_environment()
    assert isinstance(env, client.ClientEnvironment)
    assert isinstance(env.network_type, client.NetworkType)
    assert isinstance(env.network_bandwidth, client.NetworkBandwidth)
    assert isinstance(env.network_latency, client.NetworkLatency)
    assert isinstance(env.device_speed, client.DeviceSpeed)
