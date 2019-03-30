from blaze.config import train

class TestResourceType():
  def test_has_int_type(self):
    for val in list(train.ResourceType):
      assert isinstance(val, int)

class TestResource():
  def test_compiles(self):
    r = train.Resource(
      url='http://example.com',
      size=1024,
      order=1,
      group_id=0,
      source_id=0,
      type=train.ResourceType.HTML,
    )
    assert isinstance(r, train.Resource)

class TestPushGroup():
  def test_compiles(self):
    r = train.PushGroup(
      group_name='example.com',
      resources=[],
    )
    assert isinstance(r, train.PushGroup)

class TestTrainConfig():
  def test_compiles(self):
    r = train.TrainConfig(
      replay_dir='/replay/dir',
      request_url='http://example.com',
      push_groups=[],
    )
    assert isinstance(r, train.TrainConfig)
