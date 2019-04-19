import grpc

from blaze.config.client import get_random_client_environment
from blaze.proto import policy_service_pb2

from tests.mocks.config import get_push_groups

def get_page(url: str, client_environment = get_random_client_environment()) -> policy_service_pb2.Page:
  push_groups = get_push_groups()
  resources = [res for group in push_groups for res in group.resources]
  page_resources = [policy_service_pb2.Resource(
    url=res.url,
    size=res.size,
    type=res.type.value,
    timestamp=res.order
  ) for res in resources]
  return policy_service_pb2.Page(
    url=url,
    network_type=client_environment.network_type.value,
    device_speed=client_environment.device_speed.value,
    resources=page_resources,
  )

class MockGRPCServicerContext(grpc.ServicerContext):
  def __init__(self): pass
  def abort(self, code, details): pass
  def abort_with_status(self, status): pass
  def add_callback(self, callback): pass
  def auth_context(self): pass
  def cancel(self): pass
  def invocation_metadata(self): pass
  def is_active(self): pass
  def peer(self): pass
  def peer_identities(self): pass
  def peer_identity_key(self): pass
  def send_initial_metadata(self, initial_metadata): pass
  def set_code(self, code): pass
  def set_details(self, details): pass
  def set_trailing_metadata(self, trailing_metadata): pass
  def time_remaining(self): pass

class MockServer():
  def __init__(self):
    self.args = None
    self.kwargs = None
    self.set_policy_service_args = None
    self.set_policy_service_kwargs = None
    self.start_called = False
    self.stop_called = False

  def __call__(self, *args, **kwargs):
    self.args = args
    self.kwargs = kwargs
    return self

  def set_policy_service(self, *args, **kwargs):
    self.set_policy_service_args = args
    self.set_policy_service_kwargs = kwargs

  def start(self):
    self.start_called = True

  def stop(self):
    self.stop_called = True
