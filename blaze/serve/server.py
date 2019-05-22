""" Defines a general gRPC server that serves all defined RPCs """
from concurrent import futures

import grpc

from blaze.config.serve import ServeConfig
from blaze.proto import policy_service_pb2_grpc


class Server:
    """
    The main gRPC server class. Instantiate this class, register the services you want, and call
    start to start the gRPC server
    """

    def __init__(self, config: ServeConfig):
        self.config = config
        self.grpc_server = grpc.server(futures.ThreadPoolExecutor(max_workers=config.max_workers))
        self.server_started = False

    def set_policy_service(self, policy_service: policy_service_pb2_grpc.PolicyServiceServicer):
        """ Enables the policy service with the given policy_service """
        policy_service_pb2_grpc.add_PolicyServiceServicer_to_server(policy_service, self.grpc_server)

    def start(self):
        """ Starts the server on the configured host and port. This method does not block """
        self.grpc_server.add_insecure_port("{}:{}".format(self.config.host, self.config.port))
        self.grpc_server.start()
        self.server_started = True

    def stop(self):
        """ Stops the server """
        if self.server_started:
            self.grpc_server.stop(0)
