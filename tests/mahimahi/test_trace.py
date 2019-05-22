from blaze.mahimahi.trace import trace_for_kbps, format_trace_lines


class TestTraceForKbps:
    def test_trace_generation(self):
        kbpses = [
            1000,
            2250,
            3000,
            4000,
            6000,
            9000,
            11000,
            12000,
            15000,
            16000,
            18000,
            20000,
            24000,
            25550,
            33750,
            36000,
            42000,
            48000,
            96000,
            10800000,
        ]
        for kbps in kbpses:
            trace = trace_for_kbps(kbps)
            assert trace == sorted(trace)
            assert kbps == 12000 * len(trace) / (trace[-1] if trace else 1)

    def test_approximates_large_traces(self):
        kbpses = [(1, 0), (12001, 12000)]
        for kbps, actual in kbpses:
            trace = trace_for_kbps(kbps)
            assert actual == 12000 * len(trace) / (trace[-1] if trace else 1)


class TestFormatTraceLines:
    def test_empty_trace(self):
        trace = format_trace_lines([])
        assert trace == ""

    def test_format_trace_lines(self):
        trace_lines = trace_for_kbps(33750)
        trace_file = format_trace_lines(trace_lines)
        assert list(map(int, trace_file.split("\n"))) == trace_lines
