from blaze.action import ActionSpace
from blaze.config.client import get_random_client_environment
from blaze.environment import Environment
from blaze.model.model import ModelInstance, SavedModel
from blaze.proto import policy_service_pb2
from blaze.serve.policy_service import PolicyService

from tests.mocks.agent import MockAgent, mock_agent_with_action_space
from tests.mocks.config import get_push_groups, convert_push_groups_to_push_pairs
from tests.mocks.serve import get_page, MockGRPCServicerContext


class TestPolicyService:
    def setup(self):
        self.client_environment = get_random_client_environment()
        self.page = get_page("http://example.com", self.client_environment)
        self.push_groups = get_push_groups()
        self.trainable_push_groups = [group for group in self.push_groups if group.trainable]
        self.action_space = ActionSpace(self.trainable_push_groups)
        self.saved_model = SavedModel(mock_agent_with_action_space(self.action_space), Environment, "")

    def test_init(self):
        ps = PolicyService(self.saved_model)
        assert ps
        assert isinstance(ps, PolicyService)
        assert ps.saved_model is self.saved_model
        assert not ps.policies

    def test_get_policy(self):
        ps = PolicyService(self.saved_model)
        policy = ps.GetPolicy(self.page, MockGRPCServicerContext())
        assert policy
        assert isinstance(policy, policy_service_pb2.Policy)
        assert len(ps.policies) == 1
        assert ps.policies[self.page.url] is policy

    def test_get_policy_returns_cached(self):
        ps = PolicyService(self.saved_model)
        first_policy = ps.GetPolicy(self.page, MockGRPCServicerContext())
        second_policy = ps.GetPolicy(self.page, MockGRPCServicerContext())
        assert first_policy is second_policy
        assert len(ps.policies) == 1
        assert ps.policies[self.page.url] is first_policy

    def test_create_push_policy(self):
        ps = PolicyService(self.saved_model)
        policy = ps.create_push_policy(self.page)
        assert policy
        assert isinstance(policy, policy_service_pb2.Policy)
        push_pairs = convert_push_groups_to_push_pairs(self.push_groups)
        push_pairs = [(s.url, p.url) for (s, p) in push_pairs]
        for policy_entry in policy.policy:
            for push_resource in policy_entry.push_resources:
                assert (policy_entry.source_url, push_resource.url) in push_pairs

    def test_create_model_instance(self):
        ps = PolicyService(self.saved_model)
        model_instance = ps.create_model_instance(self.page)
        assert isinstance(model_instance, ModelInstance)
        assert isinstance(model_instance.agent, MockAgent)
        assert model_instance.client_environment.network_type == self.client_environment.network_type
        assert model_instance.client_environment.device_speed == self.client_environment.device_speed
        assert model_instance.env_config.push_groups == self.push_groups
