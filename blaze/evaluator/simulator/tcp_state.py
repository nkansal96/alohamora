"""
This module defines the TCPState class, which is a rudimentary simulation of TCP window
dynamics
"""

import math

INITIAL_WINDOW_SIZE = 10
MTU_BYTES = 1500
RTO_MS = 200.0


class TCPState:
    """
    Keeps track of the TCP connection state, in particular the window size (to compute the number
    of bytes that can be sent in a single round trip, and how many round trips are needed for some
    payload) and the time since last transmission (affects the shrinkage rate of the window)
    """

    def __init__(self, loss_prop: float = 0.0, cwnd: int = INITIAL_WINDOW_SIZE, time_since_last_byte: int = 0):
        self.loss_prop = loss_prop
        self.total_packets = 0
        self.cwnd = cwnd
        self.time_since_last_byte = time_since_last_byte

    @property
    def window_size(self) -> int:
        """
        :return: the current since of the window in number of packets
        """
        while self.time_since_last_byte >= RTO_MS:
            self.cwnd = max(INITIAL_WINDOW_SIZE, self.cwnd // 2)
            self.time_since_last_byte -= RTO_MS
        return self.cwnd

    @property
    def bytes_per_round_trip(self):
        """
        :return: the number of bytes that can be sent in a single round trip. This is effectively
        window size * packet size (defined to be MTU_BYTES)
        """
        return MTU_BYTES * self.window_size

    def num_packets_to_drop(self, packets_transmitted: int) -> int:
        """
        Keeps a running total to see how many packets have been transmitted and whether
        the transmission of any set packets should result in packets being dropped
        """
        self.total_packets += packets_transmitted
        if self.loss_prop < 0.00001:
            return False
        num_to_drop = self.total_packets // int(1.0 / self.loss_prop)
        if num_to_drop > 0:
            self.total_packets %= int(1.0 / self.loss_prop)
        return num_to_drop

    def round_trips_needed_for_bytes(self, bytes_to_send: int) -> int:
        """
        Computes the number of round trips needed to send the given number of bytes. It assumes
        no packet loss and that all acks are received before RTO_MS. Thus, the number of round
        trips accounts for increasing window size as bytes are sent.

        :param bytes_to_send: The number of bytes to send
        :return: the whole number of round trips necessary to send the bytes
        """
        window_size = self.window_size
        round_trips = 0
        while bytes_to_send > 0:
            bytes_to_send -= window_size * MTU_BYTES
            window_size *= 2
            round_trips += 1
        return round_trips

    def add_time_since_last_byte(self, time_ms: float):
        """
        Adds the given time since the last byte sent to the internal timer so that the window
        size can be reduced as necessary
        :param time_ms: the time in milliseconds to add to time_since_last_byte
        """
        self.time_since_last_byte += time_ms

    def add_bytes_sent(self, bytes_sent: int):
        """
        Records that a certain number of bytes were sent. This increases the window size
        by the number of packets that were used to send the bytes (corresponding to ACKs)
        and resets the time_since_last_byte

        :param bytes_sent: the number of bytes sent
        """
        # NB: if this is inaccurate, then save these bytes and aggregate them across
        #     multiple calls, then add them to cwnd when the next window_size is computed.
        self.time_since_last_byte = 0
        self.cwnd += math.ceil(bytes_sent / MTU_BYTES)
