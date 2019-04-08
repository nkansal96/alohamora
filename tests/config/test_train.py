from blaze.config.environment import PushGroup, Resource, ResourceType, EnvironmentConfig

def create_resource(url):
  return Resource(
    url=url,
    size=1024,
    order=1,
    group_id=0,
    source_id=0,
    type=ResourceType.HTML,
  )
class TestResourceType():
  def test_has_int_type(self):
    for val in list(ResourceType):
      assert isinstance(val, int)

class TestResource():
  def test_compiles(self):
    r = create_resource('http://example.com')
    assert isinstance(r, Resource)

  def test_equality(self):
    r_1 = create_resource('http://example.com')
    r_2 = create_resource('http://example.com')
    r_3 = create_resource('http://example.com/test')
    assert r_1 is not r_2
    assert r_1 is not r_3
    assert r_1 == r_2
    assert r_1 != r_3
    assert len(set([r_1, r_2, r_3])) == 2

class TestPushGroup():
  def test_compiles(self):
    r = PushGroup(
      group_name='example.com',
      resources=[],
    )
    assert isinstance(r, PushGroup)

class TestEnvironmentConfig():
  def test_compiles(self):
    r = EnvironmentConfig(
      replay_dir='/replay/dir',
      request_url='http://example.com',
      push_groups=[],
    )
    assert isinstance(r, EnvironmentConfig)
