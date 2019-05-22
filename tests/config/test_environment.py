import tempfile
from blaze.config.environment import PushGroup, Resource, ResourceType, EnvironmentConfig
from tests.mocks.config import get_env_config


def create_resource(url):
    return Resource(url=url, size=1024, order=1, group_id=0, source_id=0, type=ResourceType.HTML)


class TestResourceType:
    def test_has_int_type(self):
        for val in list(ResourceType):
            assert isinstance(val, int)


class TestResource:
    def test_compiles(self):
        r = create_resource("http://example.com")
        assert isinstance(r, Resource)

    def test_equality(self):
        r_1 = create_resource("http://example.com")
        r_2 = create_resource("http://example.com")
        r_3 = create_resource("http://example.com/test")
        assert r_1 is not r_2
        assert r_1 is not r_3
        assert r_1 == r_2
        assert r_1 != r_3
        assert len(set([r_1, r_2, r_3])) == 2


class TestPushGroup:
    def test_compiles(self):
        p = PushGroup(id=0, name="example.com", resources=[])
        assert isinstance(p, PushGroup)


class TestEnvironmentConfig:
    def test_compiles(self):
        c = EnvironmentConfig(replay_dir="/replay/dir", request_url="http://example.com", push_groups=[])
        assert isinstance(c, EnvironmentConfig)

    def test_pickle(self):
        c = get_env_config()
        with tempfile.NamedTemporaryFile() as tmp_file:
            c.save_file(tmp_file.name)
            loaded_c = EnvironmentConfig.load_file(tmp_file.name)
            assert c.request_url == loaded_c.request_url
            assert c.replay_dir == loaded_c.replay_dir
            assert len(c.push_groups) == len(loaded_c.push_groups)
            for i, group in enumerate(c.push_groups):
                assert loaded_c.push_groups[i].name == group.name
                assert len(loaded_c.push_groups[i].resources) == len(group.resources)
                for j, res in enumerate(group.resources):
                    assert loaded_c.push_groups[i].resources[j] == res
