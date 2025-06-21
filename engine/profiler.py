"""Performance profiling and timing utilities."""

import time
import csv
import statistics
from typing import Dict, List, Optional, Any
from contextlib import contextmanager
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class ProfileData:
    """Profile data for a specific operation."""
    name: str
    total_time: float = 0.0
    call_count: int = 0
    min_time: float = float('inf')
    max_time: float = 0.0
    times: List[float] = field(default_factory=list)
    
    def add_time(self, elapsed: float) -> None:
        """Add a timing measurement."""
        self.total_time += elapsed
        self.call_count += 1
        self.min_time = min(self.min_time, elapsed)
        self.max_time = max(self.max_time, elapsed)
        self.times.append(elapsed)
        
        # Keep only recent times to prevent memory bloat
        if len(self.times) > 1000:
            self.times = self.times[-500:]  # Keep last 500
            
    @property
    def average_time(self) -> float:
        """Get average time per call."""
        return self.total_time / max(1, self.call_count)
        
    @property
    def median_time(self) -> float:
        """Get median time."""
        return statistics.median(self.times) if self.times else 0.0
        
    @property
    def std_deviation(self) -> float:
        """Get standard deviation of times."""
        return statistics.stdev(self.times) if len(self.times) > 1 else 0.0


class ProfileContext:
    """Context manager for timing code blocks."""
    
    def __init__(self, profiler: 'Profiler', name: str):
        """Initialize profile context.
        
        Args:
            profiler: Profiler instance to report to
            name: Name of the operation being profiled
        """
        self.profiler = profiler
        self.name = name
        self.start_time = 0.0
        self.elapsed_time = 0.0
        
    def __enter__(self) -> 'ProfileContext':
        """Start timing."""
        self.start_time = time.perf_counter()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """End timing and record result."""
        self.elapsed_time = time.perf_counter() - self.start_time
        self.profiler.add_time(self.name, self.elapsed_time)


class Profiler:
    """High-performance profiler with CSV export and statistics.
    
    Provides context managers for timing code blocks and comprehensive
    statistics for performance analysis.
    """
    
    def __init__(self, max_recent_samples: int = 1000):
        """Initialize profiler.
        
        Args:
            max_recent_samples: Maximum recent samples to keep per operation
        """
        self.profiles: Dict[str, ProfileData] = {}
        self.max_recent_samples = max_recent_samples
        self.enabled = True
        
        # Global timing
        self.start_time = time.perf_counter()
        
    def enable(self) -> None:
        """Enable profiling."""
        self.enabled = True
        
    def disable(self) -> None:
        """Disable profiling."""
        self.enabled = False
        
    @contextmanager
    def profile(self, name: str):
        """Context manager for profiling a code block.
        
        Args:
            name: Name of the operation being profiled
            
        Usage:
            with profiler.profile("update_snakes"):
                # Code to profile
                pass
        """
        if not self.enabled:
            yield ProfileContext(self, name)
            return
            
        context = ProfileContext(self, name)
        yield context
        
    def add_time(self, name: str, elapsed_time: float) -> None:
        """Add timing data for an operation.
        
        Args:
            name: Operation name
            elapsed_time: Elapsed time in seconds
        """
        if not self.enabled:
            return
            
        if name not in self.profiles:
            self.profiles[name] = ProfileData(name)
            
        self.profiles[name].add_time(elapsed_time)
        
    def get_profile(self, name: str) -> Optional[ProfileData]:
        """Get profile data for an operation.
        
        Args:
            name: Operation name
            
        Returns:
            ProfileData or None if not found
        """
        return self.profiles.get(name)
        
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive profiling summary.
        
        Returns:
            Dictionary with profiling statistics
        """
        summary = {
            'total_operations': len(self.profiles),
            'profiler_uptime': time.perf_counter() - self.start_time,
            'enabled': self.enabled,
            'operations': {}
        }
        
        for name, profile in self.profiles.items():
            summary['operations'][name] = {
                'total_time': profile.total_time,
                'call_count': profile.call_count,
                'average_time': profile.average_time,
                'min_time': profile.min_time,
                'max_time': profile.max_time,
                'median_time': profile.median_time,
                'std_deviation': profile.std_deviation,
                'percentage_of_total': 0.0  # Will be calculated below
            }
            
        # Calculate percentages
        total_time = sum(p.total_time for p in self.profiles.values())
        if total_time > 0:
            for name in summary['operations']:
                percentage = (summary['operations'][name]['total_time'] / total_time) * 100
                summary['operations'][name]['percentage_of_total'] = percentage
                
        return summary
        
    def get_sorted_profiles(self, sort_by: str = 'total_time') -> List[ProfileData]:
        """Get profiles sorted by specified metric.
        
        Args:
            sort_by: Metric to sort by ('total_time', 'average_time', 'call_count')
            
        Returns:
            List of ProfileData sorted by metric
        """
        if sort_by == 'total_time':
            return sorted(self.profiles.values(), key=lambda p: p.total_time, reverse=True)
        elif sort_by == 'average_time':
            return sorted(self.profiles.values(), key=lambda p: p.average_time, reverse=True)
        elif sort_by == 'call_count':
            return sorted(self.profiles.values(), key=lambda p: p.call_count, reverse=True)
        else:
            return list(self.profiles.values())
            
    def print_summary(self, top_n: int = 10) -> None:
        """Print a formatted summary of profiling data.
        
        Args:
            top_n: Number of top operations to display
        """
        print(f"\\n=== Profiler Summary (Top {top_n}) ===")
        print(f"Uptime: {time.perf_counter() - self.start_time:.2f}s")
        print(f"Operations tracked: {len(self.profiles)}")
        print()
        
        profiles = self.get_sorted_profiles('total_time')[:top_n]
        
        print(f"{'Operation':<20} {'Total(ms)':<10} {'Calls':<8} {'Avg(ms)':<10} {'Min(ms)':<10} {'Max(ms)':<10}")
        print("-" * 80)
        
        for profile in profiles:
            print(f"{profile.name:<20} "
                  f"{profile.total_time*1000:<10.2f} "
                  f"{profile.call_count:<8} "
                  f"{profile.average_time*1000:<10.3f} "
                  f"{profile.min_time*1000:<10.3f} "
                  f"{profile.max_time*1000:<10.3f}")
                  
    def export_csv(self, filename: str) -> None:
        """Export profiling data to CSV file.
        
        Args:
            filename: Output CSV filename
        """
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            
            # Header
            writer.writerow([
                'Operation', 'Total_Time_ms', 'Call_Count', 'Average_Time_ms',
                'Min_Time_ms', 'Max_Time_ms', 'Median_Time_ms', 'Std_Deviation_ms'
            ])
            
            # Data rows
            for profile in self.get_sorted_profiles('total_time'):
                writer.writerow([
                    profile.name,
                    profile.total_time * 1000,
                    profile.call_count,
                    profile.average_time * 1000,
                    profile.min_time * 1000,
                    profile.max_time * 1000,
                    profile.median_time * 1000,
                    profile.std_deviation * 1000
                ])
                
    def export_frame_times_csv(self, filename: str, operation: str) -> None:
        """Export individual frame times for an operation to CSV.
        
        Args:
            filename: Output CSV filename
            operation: Operation name to export
        """
        profile = self.profiles.get(operation)
        if not profile:
            return
            
        with open(filename, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(['Frame', 'Time_ms'])
            
            for i, time_val in enumerate(profile.times):
                writer.writerow([i, time_val * 1000])
                
    def reset(self) -> None:
        """Reset all profiling data."""
        self.profiles.clear()
        self.start_time = time.perf_counter()
        
    def reset_operation(self, name: str) -> None:
        """Reset profiling data for a specific operation.
        
        Args:
            name: Operation name to reset
        """
        if name in self.profiles:
            del self.profiles[name]
            
    def get_operation_names(self) -> List[str]:
        """Get list of all tracked operation names.
        
        Returns:
            List of operation names
        """
        return list(self.profiles.keys())
        
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"Profiler(operations={len(self.profiles)}, "
                f"enabled={self.enabled}, uptime={time.perf_counter() - self.start_time:.1f}s)")
