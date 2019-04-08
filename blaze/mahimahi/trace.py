""" Utility functions for creating and processing Mahimahi trace files """
from fractions import Fraction
from typing import List

BITS_PER_BYTE = 8
PACKET_SIZE = 1500 * BITS_PER_BYTE
MAX_TRACE_MS = 1000

def trace_for_kbps(kbps: int) -> List[int]:
  """ Returns Mahimahi trace lines whose average kbps approximates the passed in value """
  # - convert kbps to a Fraction representing # packets per line of a Mahimahi trace file
  # - Fraction will also simplify the ratio, giving us exactly how many lines we need and what
  #   the total ms duration of the trace
  # - limit the denominator to 100 so that we don't generate arbitrarily large trace files
  ratio = Fraction(numerator=kbps, denominator=PACKET_SIZE).limit_denominator(MAX_TRACE_MS)

  # the numerator gives the number of lines (total packets) to deliver
  num_lines = ratio.numerator
  # the denominator gives the maximum line value (aka the largest time offset from the start
  # of the trace) to deliver all packets within. Since Mahimahi traces wrap around, we can view
  # the trace as a rate. Taking num_lines/max_line will give us packets/ms --> kbps exactly, as expected
  max_line = ratio.denominator

  # if the number of lines is 1, just return the max_line value as there is no other solution.
  # this essentially corresponds to saying send 1 packet every `max_line` milliseconds
  if num_lines == 1:
    return [max_line]

  trace_lines = []
  for i in range(1, max_line + 1):
    # compute the number of packets that should be delivered at time offset i
    n_times = num_lines//max_line + ((max_line - i) < (num_lines % max_line))
    trace_lines.extend([i] * n_times)
  return trace_lines

def format_trace_lines(trace_lines: List[int]) -> str:
  """
  Formats a list of Mahimahi trace lines into a trace file format. This function
  should be used with the output from trace_for_kbps
  """
  return '\n'.join(map(str, trace_lines))
