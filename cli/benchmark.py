"""Benchmarking tool for performance analysis and optimization."""

import time
import statistics
import json
import argparse
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
import psutil
import gc

from cli.simulate import HeadlessSimulation


@dataclass
class BenchmarkResult:
    """Results from a single benchmark run."""
    config: Dict[str, Any]
    avg_fps: float
    min_fps: float
    max_fps: float
    std_fps: float
    avg_frame_time: float
    memory_usage: float
    cpu_usage: float
    duration: float
    frames_completed: int
    success: bool
    error: str = ""


class PerformanceBenchmark:
    """Comprehensive performance benchmarking tool.
    
    Tests various configurations and measures performance metrics
    to identify bottlenecks and optimal settings.
    """
    
    def __init__(self):
        """Initialize benchmark suite."""
        self.results: List[BenchmarkResult] = []
        self.baseline_config = {
            "num_snakes": 100,
            "grid_size": 256,
            "duration": 30,
            "target_fps": 60,
            "seed": 42,
        }
        
    def run_single_benchmark(self, config: Dict[str, Any]) -> BenchmarkResult:
        """Run a single benchmark configuration.
        
        Args:
            config: Configuration to test
            
        Returns:
            BenchmarkResult with performance metrics
        """
        print(f"Running benchmark: {config}")
        
        # Monitor system resources
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        try:
            # Force garbage collection before test
            gc.collect()
            
            # Run simulation
            simulation = HeadlessSimulation(config)
            start_time = time.time()
            stats = simulation.run()
            end_time = time.time()
            
            # Calculate performance metrics
            frame_stats = stats['frames']
            if not frame_stats:
                raise ValueError("No frame data collected")
                
            fps_values = [f['fps'] for f in frame_stats if f['fps'] > 0]
            frame_times = [f['total_time'] for f in frame_stats]
            
            # System resource usage
            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            memory_usage = final_memory - initial_memory
            cpu_usage = process.cpu_percent()
            
            result = BenchmarkResult(
                config=config.copy(),
                avg_fps=statistics.mean(fps_values) if fps_values else 0,
                min_fps=min(fps_values) if fps_values else 0,
                max_fps=max(fps_values) if fps_values else 0,
                std_fps=statistics.stdev(fps_values) if len(fps_values) > 1 else 0,
                avg_frame_time=statistics.mean(frame_times) if frame_times else 0,
                memory_usage=memory_usage,
                cpu_usage=cpu_usage,
                duration=end_time - start_time,
                frames_completed=len(frame_stats),
                success=True
            )
            
        except Exception as e:
            result = BenchmarkResult(
                config=config.copy(),
                avg_fps=0,
                min_fps=0,
                max_fps=0,
                std_fps=0,
                avg_frame_time=0,
                memory_usage=0,
                cpu_usage=0,
                duration=0,
                frames_completed=0,
                success=False,
                error=str(e)
            )
            
        return result
        
    def benchmark_scale_test(self, snake_counts: List[int]) -> List[BenchmarkResult]:
        """Benchmark performance across different snake counts.
        
        Args:
            snake_counts: List of snake counts to test
            
        Returns:
            List of benchmark results
        """
        print("\\n=== Scale Test ===")
        results = []
        
        for count in snake_counts:
            config = self.baseline_config.copy()
            config["num_snakes"] = count
            config["duration"] = 20  # Shorter duration for scale test
            
            result = self.run_single_benchmark(config)
            results.append(result)
            
            if result.success:
                print(f"  {count} snakes: {result.avg_fps:.1f} FPS, "
                      f"{result.memory_usage:.1f} MB memory")
            else:
                print(f"  {count} snakes: FAILED - {result.error}")
                
        return results
        
    def benchmark_grid_size_test(self, grid_sizes: List[int]) -> List[BenchmarkResult]:
        """Benchmark performance across different grid sizes.
        
        Args:
            grid_sizes: List of grid sizes to test
            
        Returns:
            List of benchmark results
        """
        print("\\n=== Grid Size Test ===")
        results = []
        
        for size in grid_sizes:
            config = self.baseline_config.copy()
            config["grid_size"] = size
            config["duration"] = 20
            
            result = self.run_single_benchmark(config)
            results.append(result)
            
            if result.success:
                print(f"  {size}x{size} grid: {result.avg_fps:.1f} FPS, "
                      f"{result.memory_usage:.1f} MB memory")
            else:
                print(f"  {size}x{size} grid: FAILED - {result.error}")
                
        return results
        
    def benchmark_endurance_test(self, duration: int = 300) -> BenchmarkResult:
        """Long-running endurance test.
        
        Args:
            duration: Test duration in seconds
            
        Returns:
            Benchmark result
        """
        print(f"\\n=== Endurance Test ({duration}s) ===")
        
        config = self.baseline_config.copy()
        config["duration"] = duration
        config["num_snakes"] = 1000
        
        return self.run_single_benchmark(config)
        
    def benchmark_stress_test(self) -> BenchmarkResult:
        """Maximum stress test with high snake count.
        
        Returns:
            Benchmark result
        """
        print("\\n=== Stress Test ===")
        
        config = self.baseline_config.copy()
        config["num_snakes"] = 5000
        config["duration"] = 60
        
        return self.run_single_benchmark(config)
        
    def run_comprehensive_benchmark(self) -> Dict[str, Any]:
        """Run comprehensive benchmark suite.
        
        Returns:
            Complete benchmark results
        """
        print("Starting comprehensive benchmark suite...")
        start_time = time.time()
        
        # Baseline test
        print("\\n=== Baseline Test ===")
        baseline_result = self.run_single_benchmark(self.baseline_config)
        
        # Scale tests
        scale_results = self.benchmark_scale_test([50, 100, 250, 500, 1000, 2000])
        
        # Grid size tests  
        grid_results = self.benchmark_grid_size_test([128, 256, 512])
        
        # Endurance test
        endurance_result = self.benchmark_endurance_test(120)  # 2 minutes
        
        # Stress test
        stress_result = self.benchmark_stress_test()
        
        end_time = time.time()
        
        # Compile results
        all_results = {
            "benchmark_duration": end_time - start_time,
            "baseline": baseline_result,
            "scale_tests": scale_results,
            "grid_size_tests": grid_results,
            "endurance_test": endurance_result,
            "stress_test": stress_result,
            "system_info": self.get_system_info(),
        }
        
        return all_results
        
    def get_system_info(self) -> Dict[str, Any]:
        """Get system information for benchmark context.
        
        Returns:
            System information dictionary
        """
        return {
            "cpu_count": psutil.cpu_count(),            "cpu_freq": psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {},
            "memory_total": psutil.virtual_memory().total / 1024 / 1024 / 1024,  # GB
            "memory_available": psutil.virtual_memory().available / 1024 / 1024 / 1024,  # GB
            "python_version": __import__('sys').version,
        }
        
    def print_summary(self, results: Dict[str, Any]) -> None:
        """Print benchmark summary.
        
        Args:
            results: Complete benchmark results
        """
        print("\n" + "="*60)
        print("BENCHMARK SUMMARY")
        print("="*60)
        
        print(f"Total benchmark time: {results.get('benchmark_duration', 0):.1f}s")
        
        # System info (if available)
        if 'system_info' in results:
            system_info = results['system_info']
            print(f"System: {system_info['cpu_count']} CPU cores, "
                  f"{system_info['memory_total']:.1f} GB RAM")
          # Handle different result types
        if 'quick_test' in results:
            # Quick test results
            result = results['quick_test']
            print(f"\nQuick Test Result:")
            if result.success:
                print(f"  ✅ {result.config['num_snakes']} snakes: {result.avg_fps:.1f} FPS")
                print(f"  📊 Memory usage: {result.memory_usage:.1f} MB")
                print(f"  ⏱️  Frame time: {result.avg_frame_time:.1f}ms")
            else:
                print(f"  ❌ Test failed: {result.error}")
            return
        
        # Scale test only results
        if 'scale_tests' in results and 'baseline' not in results:
            scale_results = results['scale_tests']
            print(f"\nScale Test Results:")
            for result in scale_results:
                if result.success:
                    print(f"  ✅ {result.config['num_snakes']} snakes: {result.avg_fps:.1f} FPS")
                else:
                    print(f"  ❌ {result.config['num_snakes']} snakes: FAILED")
            return
            
        # Full comprehensive results
        if 'baseline' in results:
            baseline = results['baseline']
            print(f"\nBaseline ({baseline.config['num_snakes']} snakes): "
                  f"{baseline.avg_fps:.1f} FPS")
        
        # Scale test summary
        if 'scale_tests' in results:
            scale_results = results['scale_tests']
        successful_scales = [r for r in scale_results if r.success]
        if successful_scales:
            best_scale = max(successful_scales, key=lambda r: r.avg_fps)
            print(f"Best scale performance: {best_scale.config['num_snakes']} snakes "
                  f"at {best_scale.avg_fps:.1f} FPS")
                  
        # Stress test
        stress = results['stress_test']
        if stress.success:
            print(f"Stress test (5000 snakes): {stress.avg_fps:.1f} FPS")
        else:
            print(f"Stress test: FAILED - {stress.error}")
            
        # Performance recommendations
        print("\\nRECOMMENDATIONS:")
        
        if baseline.avg_fps < 30:
            print("- Consider reducing snake count or grid size")
        elif baseline.avg_fps > 120:
            print("- System can handle increased load")
            
        if any(r.memory_usage > 1000 for r in scale_results if r.success):
            print("- High memory usage detected with large snake counts")
            
        print("\\n" + "="*60)
        
    def save_results(self, results: Dict[str, Any], filename: str) -> None:
        """Save benchmark results to file.
        
        Args:
            results: Benchmark results to save
            filename: Output filename
        """
        # Convert dataclass objects to dictionaries for JSON serialization
        def convert_result(obj):
            if isinstance(obj, BenchmarkResult):
                return obj.__dict__
            elif isinstance(obj, list):
                return [convert_result(item) for item in obj]
            elif isinstance(obj, dict):
                return {k: convert_result(v) for k, v in obj.items()}
            else:
                return obj
                
        serializable_results = convert_result(results)
        
        with open(filename, 'w') as f:
            json.dump(serializable_results, f, indent=2)
            
        print(f"Benchmark results saved to {filename}")


def main():
    """Main entry point for benchmark tool."""
    parser = argparse.ArgumentParser(description="Ouroboros Ops Performance Benchmark")
    parser.add_argument("--quick", action="store_true", help="Run quick benchmark")
    parser.add_argument("--scale-only", action="store_true", help="Run only scale test")
    parser.add_argument("--max-snakes", type=int, default=2000, help="Maximum snakes for scale test")
    parser.add_argument("--output", type=str, default="benchmark_results.json", help="Output file")
    parser.add_argument("--duration", type=int, default=30, help="Test duration per configuration")
    
    args = parser.parse_args()
    
    benchmark = PerformanceBenchmark()
    
    if args.quick:
        # Quick benchmark with reduced parameters
        start_time = time.time()
        config = benchmark.baseline_config.copy()
        config["duration"] = 15
        quick_result = benchmark.run_single_benchmark(config)
        end_time = time.time()
        
        results = {
            "quick_test": quick_result,
            "benchmark_duration": end_time - start_time,
            "system_info": benchmark.get_system_info()
        }
        
    elif args.scale_only:
        # Scale test only
        start_time = time.time()
        snake_counts = [100, 250, 500, 1000, args.max_snakes]
        scale_results = benchmark.benchmark_scale_test(snake_counts)
        end_time = time.time()
        
        results = {
            "scale_tests": scale_results,
            "benchmark_duration": end_time - start_time,
            "system_info": benchmark.get_system_info()
        }
        
    else:
        # Full comprehensive benchmark
        results = benchmark.run_comprehensive_benchmark()
        
    # Print and save results
    benchmark.print_summary(results)
    benchmark.save_results(results, args.output)


if __name__ == "__main__":
    main()
