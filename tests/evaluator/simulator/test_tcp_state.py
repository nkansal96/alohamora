import random

from blaze.evaluator.simulator.tcp_state import INITIAL_WINDOW_SIZE, MTU_BYTES, RTO_MS, TCPState


class TestTCPState:
    def test_default_window_size(self):
        tcp_state = TCPState()
        assert tcp_state.window_size == INITIAL_WINDOW_SIZE
        assert tcp_state.time_since_last_byte == 0

    def test_window_size_less_than_rto(self):
        tcp_state = TCPState(cwnd=INITIAL_WINDOW_SIZE * 2, time_since_last_byte=RTO_MS / 2)
        assert tcp_state.window_size == INITIAL_WINDOW_SIZE * 2
        assert tcp_state.time_since_last_byte == RTO_MS / 2

    def test_window_size_more_than_rto(self):
        tcp_state = TCPState(cwnd=INITIAL_WINDOW_SIZE * 2, time_since_last_byte=3 * RTO_MS / 2)
        assert tcp_state.window_size == INITIAL_WINDOW_SIZE
        assert tcp_state.time_since_last_byte == RTO_MS / 2

    def test_window_size_several_rto(self):
        tcp_state = TCPState(cwnd=INITIAL_WINDOW_SIZE * 8, time_since_last_byte=3 * RTO_MS)
        assert tcp_state.window_size == INITIAL_WINDOW_SIZE
        assert tcp_state.time_since_last_byte == 0

    def test_window_size_stays_above_initial_window_size(self):
        tcp_state = TCPState(time_since_last_byte=3 * RTO_MS / 2)
        assert tcp_state.window_size == INITIAL_WINDOW_SIZE
        assert tcp_state.time_since_last_byte == RTO_MS / 2

    def test_window_size_stays_above_initial_window_size_multiple_rto(self):
        tcp_state = TCPState(cwnd=INITIAL_WINDOW_SIZE * 4, time_since_last_byte=4 * RTO_MS)
        assert tcp_state.window_size == INITIAL_WINDOW_SIZE
        assert tcp_state.time_since_last_byte == 0

    def test_default_bytes_per_round_trip(self):
        tcp_state = TCPState()
        assert tcp_state.bytes_per_round_trip == MTU_BYTES * INITIAL_WINDOW_SIZE

    def test_bytes_per_round_trip_rto(self):
        tcp_state = TCPState(cwnd=INITIAL_WINDOW_SIZE * 2, time_since_last_byte=4 * RTO_MS)
        assert tcp_state.bytes_per_round_trip == MTU_BYTES * INITIAL_WINDOW_SIZE

        tcp_state = TCPState(cwnd=INITIAL_WINDOW_SIZE * 8, time_since_last_byte=RTO_MS)
        assert tcp_state.bytes_per_round_trip == 4 * MTU_BYTES * INITIAL_WINDOW_SIZE

    def test_round_trips_needed_for_zero_bytes(self):
        tcp_state = TCPState()
        assert tcp_state.round_trips_needed_for_bytes(0) == 0

    def test_default_round_trips_needed_for_bytes(self):
        tcp_state = TCPState()
        # Since each value is <= MTU_BYTES * INITIAL_WINDOW_SIZE, expect the answer to be 1
        bytes_to_send_tests = [
            MTU_BYTES * INITIAL_WINDOW_SIZE,
            *[random.randint(1, MTU_BYTES * INITIAL_WINDOW_SIZE) for i in range(100)],
        ]
        for bytes_to_send in bytes_to_send_tests:
            assert tcp_state.round_trips_needed_for_bytes(bytes_to_send) == 1

    def test_round_trips_needed_for_bytes_adjusts_based_on_rto(self):
        tcp_state = TCPState(cwnd=INITIAL_WINDOW_SIZE * 2, time_since_last_byte=4 * RTO_MS)
        # Since each value is <= MTU_BYTES * INITIAL_WINDOW_SIZE, expect the answer to be 1
        bytes_to_send_tests = [
            MTU_BYTES * INITIAL_WINDOW_SIZE,
            *[random.randint(1, MTU_BYTES * INITIAL_WINDOW_SIZE) for i in range(100)],
        ]
        for bytes_to_send in bytes_to_send_tests:
            assert tcp_state.round_trips_needed_for_bytes(bytes_to_send) == 1

        assert tcp_state.round_trips_needed_for_bytes(MTU_BYTES * INITIAL_WINDOW_SIZE + 1) == 2

    def test_round_trips_needed_for_bytes_adjusts_based_on_cwnd(self):
        tcp_state = TCPState(cwnd=INITIAL_WINDOW_SIZE * 2)
        # Since cwnd is 2*INITIAL_WINDOW_SIZE, need only 1 rtt for these values
        bytes_to_send_tests = [
            2 * MTU_BYTES * INITIAL_WINDOW_SIZE,
            *[random.randint(1, 2 * MTU_BYTES * INITIAL_WINDOW_SIZE) for i in range(100)],
        ]
        for bytes_to_send in bytes_to_send_tests:
            assert tcp_state.round_trips_needed_for_bytes(bytes_to_send) == 1
        assert tcp_state.round_trips_needed_for_bytes(2 * MTU_BYTES * INITIAL_WINDOW_SIZE + 1) == 2

    def test_round_trips_needed_for_bytes_increases_window_size(self):
        tcp_state = TCPState()
        bytes_to_send = 8 * MTU_BYTES * INITIAL_WINDOW_SIZE
        # First RTT sends INITIAL_WINDOW_SIZE packets, second sends 2, third sends 4, so we need 4 RTT
        assert tcp_state.round_trips_needed_for_bytes(bytes_to_send) == 4

    def test_add_time_since_last_byte(self):
        tcp_state = TCPState(cwnd=INITIAL_WINDOW_SIZE * 2, time_since_last_byte=12)
        tcp_state.add_time_since_last_byte(88)
        assert tcp_state.time_since_last_byte == 100
        assert tcp_state.window_size == INITIAL_WINDOW_SIZE * 2

        tcp_state.add_time_since_last_byte(RTO_MS - 100)
        assert tcp_state.time_since_last_byte == RTO_MS
        assert tcp_state.window_size == INITIAL_WINDOW_SIZE
        assert tcp_state.time_since_last_byte == 0

    def test_add_bytes_sent(self):
        tcp_state = TCPState(time_since_last_byte=100)
        tcp_state.add_bytes_sent(100)
        assert tcp_state.time_since_last_byte == 0
        assert tcp_state.window_size == INITIAL_WINDOW_SIZE + 1

    def test_add_bytes_sent_more_than_mtu(self):
        tcp_state = TCPState()
        tcp_state.add_bytes_sent(MTU_BYTES * 3.5)
        assert tcp_state.window_size == INITIAL_WINDOW_SIZE + 4

    def test_packets_not_dropped_if_prop_is_zero(self):
        tcp_state = TCPState()
        assert tcp_state.num_packets_to_drop(10000) == 0

    def test_packets_dropped_if_prop_gt_zero(self):
        tcp_state = TCPState(loss_prop=0.01)
        assert tcp_state.num_packets_to_drop(10) == 0
        assert tcp_state.num_packets_to_drop(20) == 0
        assert tcp_state.num_packets_to_drop(50) == 0
        assert tcp_state.num_packets_to_drop(20) == 1

        assert tcp_state.num_packets_to_drop(10) == 0
        assert tcp_state.num_packets_to_drop(99) == 1
        assert tcp_state.num_packets_to_drop(91) == 1
        assert tcp_state.num_packets_to_drop(1000) == 10
