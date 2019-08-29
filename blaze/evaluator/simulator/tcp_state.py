"""
This module defines the classes and methods to implement a way to simulate
loading a webpage and simulating its page load time from a dependency graph
"""

import math

INITIAL_WINDOW_SIZE = 10
MTU_BYTES = 1500
RTO_MS = 200.0


class TCPState:
    def __init__(self, cwnd: int = INITIAL_WINDOW_SIZE, time_since_last_byte: int = 0):
        self.cwnd = cwnd
        self.time_since_last_byte = time_since_last_byte

    @property
    def window_size(self):
        while self.time_since_last_byte >= RTO_MS:
            self.cwnd = max(INITIAL_WINDOW_SIZE, self.cwnd / 2)
            self.time_since_last_byte -= RTO_MS
        return self.cwnd

    @property
    def bytes_per_round_trip(self):
        return MTU_BYTES * self.window_size

    def round_trips_needed_for_bytes(self, bytes_to_send: int) -> int:
        # Assuming no packet loss and that we receive all acks before RTO
        window_size = self.window_size
        round_trips = 0
        while bytes_to_send > 0:
            bytes_to_send -= window_size * MTU_BYTES
            window_size *= 2
            round_trips += 1
        return round_trips

    def add_time_since_last_byte(self, time_ms: float):
        self.time_since_last_byte += time_ms

    def add_bytes_sent(self, bytes_sent: int):
        self.time_since_last_byte = 0
        self.cwnd += math.ceil(bytes_sent / MTU_BYTES)
