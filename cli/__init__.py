"""CLI package for benchmarking and simulation tools."""

from .simulate import main as simulate_main
from .benchmark import main as benchmark_main

__all__ = ["simulate_main", "benchmark_main"]
