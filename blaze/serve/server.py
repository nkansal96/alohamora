from concurrent import futures

import grpc

from blaze.config.serve import ServeConfig
from blaze.proto import policy_service_pb2_grpc

class Server():
  def __init__(self, config: ServeConfig):
    self.config = config
    self.grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=config.max_workers))
    self.server_started = False

  def set_policy_service(self, policy_service: policy_service_pb2_grpc.PolicyServiceServicer):
    policy_service_pb2_grpc.add_PolicyServiceServicer_to_server(policy_service, self.grpc_server)

  def start(self):
    self.grpc_server.add_insecure_port("{}:{}".format(self.config.host, self.config.port))
    self.grpc_server.start()
    self.server_started = True

  def stop(self):
    if self.server_started:
      self.grpc_server.stop(0)
