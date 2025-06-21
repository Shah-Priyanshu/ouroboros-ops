"""Headless simulation tool for running tournaments and collecting statistics."""

import json
import time
import argparse
import random
from pathlib import Path
from typing import Dict, Any, List

from snake_core import Grid, Snake, FoodManager, PathFinder, SectorManager
from engine import GameLoop


class HeadlessSimulation:
    """Headless simulation for benchmarking and data collection."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize simulation with configuration.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Extract configuration
        self.grid_size = config.get('grid_size', 256)
        self.num_snakes = config.get('num_snakes', 1000)
        self.target_fps = config.get('target_fps', 60)
        self.duration = config.get('duration', 60)  # seconds
        self.seed = config.get('seed', 42)
          # Initialize components
        random.seed(self.seed)
        self.grid = Grid(self.grid_size, self.grid_size)
        self.sector_manager = SectorManager(self.grid_size, self.grid_size)
        self.food_manager = FoodManager(target_food_count=self.grid_size * 2)
        self.pathfinder = PathFinder(self.grid_size, self.grid_size)
        
        # Game state
        self.snakes: List[Snake] = []
        self.game_loop = GameLoop(target_fps=self.target_fps)
        
        # Statistics collection
        self.stats: Dict[str, Any] = {
            'config': config,
            'start_time': 0.0,
            'end_time': 0.0,
            'frames': [],
            'performance': {},
            'final_state': {}
        }
        
        # Setup callbacks
        self.game_loop.set_update_callback(self.update)
        self.game_loop.set_stats_callback(self.collect_frame_stats)
        
        self.start_time = 0.0
        self.frame_count = 0
        
    def initialize(self) -> None:
        """Initialize simulation state."""
        print(f"Initializing headless simulation: {self.grid_size}x{self.grid_size}, "
              f"{self.num_snakes} snakes, {self.duration}s")
              
        # Spawn food
        self.food_manager.spawn_food_batch(self.grid, 500)
        
        # Spawn snakes
        self.spawn_snakes()
        
        self.start_time = time.time()
        self.stats['start_time'] = self.start_time
        
    def spawn_snakes(self) -> None:
        """Spawn snakes at random positions."""
        empty_positions = self.grid.find_empty_cells()  
        spawn_count = min(self.num_snakes, len(empty_positions))
        
        for i in range(spawn_count):
            pos_idx = random.randint(0, len(empty_positions) - 1)
            start_row, start_col = empty_positions.pop(pos_idx)
            
            snake = Snake(i, start_row, start_col, initial_length=3)
            
            # Place on grid
            for seg_row, seg_col in snake.get_body_positions():
                if (seg_row, seg_col) == snake.get_head_position():
                    self.grid.set_snake_head(seg_row, seg_col)
                else:
                    self.grid.set_snake_body(seg_row, seg_col)
                    
            self.snakes.append(snake)
            
    def update(self, dt: float) -> None:
        """Update simulation state."""
        self.frame_count += 1
        
        # Update food
        with self.game_loop.profiler.profile("food_update"):
            self.food_manager.update(self.grid)
            
        # Update snakes (simplified AI)
        with self.game_loop.profiler.profile("snake_update"):
            self.update_snakes()
            
        # Check termination conditions
        if time.time() - self.start_time >= self.duration:
            self.game_loop.stop()
            
    def update_snakes(self) -> None:
        """Simple snake update logic."""
        food_positions = self.food_manager.get_food_positions(self.grid)
        alive_count = 0
        
        for snake in self.snakes:
            if snake.state.value != 0:  # Not alive
                continue
                
            alive_count += 1
            
            # Simple AI: move toward nearest food
            head_row, head_col = snake.get_head_position()
            
            if food_positions:
                # Find nearest food
                nearest_food = min(food_positions, 
                                 key=lambda f: abs(f[0] - head_row) + abs(f[1] - head_col))
                food_row, food_col = nearest_food
                
                # Simple direction decision
                dr = food_row - head_row
                dc = food_col - head_col
                
                if abs(dr) > abs(dc):
                    new_direction = 2 if dr > 0 else 0  # South or North
                else:
                    new_direction = 1 if dc > 0 else 3  # East or West
                    
                if snake.can_turn(new_direction):
                    snake.set_direction(new_direction)
                    
            # Move snake
            next_head = snake.get_next_head_position()
            ate_food = False
            
            if (0 <= next_head[0] < self.grid.height and 
                0 <= next_head[1] < self.grid.width):
                if self.grid.has_food(next_head[0], next_head[1]):
                    ate_food = self.food_manager.consume_food(self.grid, next_head[0], next_head[1])
                    
                snake.move(self.grid, ate_food)
                
        # Update alive count in stats
        if not hasattr(self, 'alive_snakes'):
            self.alive_snakes = alive_count
        else:
            self.alive_snakes = alive_count
            
    def collect_frame_stats(self, frame_stats) -> None:
        """Collect statistics for each frame."""
        stats_dict = {
            'frame': frame_stats.frame_number,
            'fps': frame_stats.fps,
            'update_time': frame_stats.update_time,
            'render_time': frame_stats.render_time,
            'total_time': frame_stats.total_time,
            'alive_snakes': getattr(self, 'alive_snakes', 0),
            'food_count': self.food_manager.get_current_food_count(self.grid),
        }
        
        self.stats['frames'].append(stats_dict)
        
        # Print progress every 60 frames (1 second)
        if frame_stats.frame_number % 60 == 0:
            elapsed = time.time() - self.start_time
            print(f"Frame {frame_stats.frame_number}: {frame_stats.fps:.1f} FPS, "
                  f"elapsed {elapsed:.1f}s, alive {stats_dict['alive_snakes']}")
                  
    def run(self) -> Dict[str, Any]:
        """Run the simulation and return statistics.
        
        Returns:
            Dictionary with complete simulation statistics
        """
        self.initialize()
        
        try:
            self.game_loop.run()
        except KeyboardInterrupt:
            print("Simulation interrupted")
            
        # Collect final statistics
        self.stats['end_time'] = time.time()
        self.stats['duration'] = self.stats['end_time'] - self.stats['start_time']
        
        # Performance summary
        self.stats['performance'] = self.game_loop.get_performance_summary()
        self.stats['performance']['profiler'] = self.game_loop.profiler.get_summary()
        
        # Component statistics
        self.stats['food_manager'] = self.food_manager.get_stats()
        self.stats['pathfinder'] = self.pathfinder.get_stats()
        self.stats['sector_manager'] = self.sector_manager.get_stats()
        
        # Final game state
        alive_snakes = sum(1 for s in self.snakes if s.state.value == 0)
        self.stats['final_state'] = {
            'alive_snakes': alive_snakes,
            'total_snakes': len(self.snakes),
            'food_count': self.food_manager.get_current_food_count(self.grid),
            'total_food_eaten': sum(s.food_eaten for s in self.snakes),
        }
        
        return self.stats
        
    def save_stats(self, filename: str) -> None:
        """Save statistics to JSON file.
        
        Args:
            filename: Output filename
        """
        with open(filename, 'w') as f:
            json.dump(self.stats, f, indent=2)
        print(f"Statistics saved to {filename}")


def run_tournament(configs: List[Dict[str, Any]], output_dir: str) -> None:
    """Run multiple simulations with different configurations.
    
    Args:
        configs: List of configuration dictionaries
        output_dir: Directory to save results
    """
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    tournament_results = []
    
    for i, config in enumerate(configs):
        print(f"\\n=== Running simulation {i+1}/{len(configs)} ===")
        
        simulation = HeadlessSimulation(config)
        stats = simulation.run()
        
        # Save individual results
        filename = output_path / f"simulation_{i+1}.json"
        simulation.save_stats(str(filename))
        
        # Add to tournament results
        tournament_results.append({
            'config': config,
            'avg_fps': stats['performance'].get('average_fps', 0),
            'duration': stats['duration'],
            'final_alive': stats['final_state']['alive_snakes'],
            'food_eaten': stats['final_state']['total_food_eaten'],
        })
        
    # Save tournament summary
    summary_file = output_path / "tournament_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(tournament_results, f, indent=2)
        
    print(f"\\nTournament complete. Results saved to {output_dir}")


def main():
    """Main entry point for simulation tool."""
    parser = argparse.ArgumentParser(description="Ouroboros Ops Headless Simulation")
    parser.add_argument("--agents", type=int, default=1000, help="Number of snakes")
    parser.add_argument("--grid-size", type=int, default=256, help="Grid size")
    parser.add_argument("--duration", type=int, default=60, help="Duration in seconds")
    parser.add_argument("--fps", type=int, default=60, help="Target FPS")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="simulation_results.json", 
                       help="Output filename")
    parser.add_argument("--tournament", action="store_true", 
                       help="Run tournament with multiple configurations")
    parser.add_argument("--tournament-dir", type=str, default="tournament_results",
                       help="Tournament results directory")
    
    args = parser.parse_args()
    
    if args.tournament:
        # Define tournament configurations
        configs = [
            {"num_snakes": 500, "grid_size": 256, "duration": 30, "seed": 42},
            {"num_snakes": 1000, "grid_size": 256, "duration": 30, "seed": 42},
            {"num_snakes": 2000, "grid_size": 256, "duration": 30, "seed": 42},
            {"num_snakes": 5000, "grid_size": 256, "duration": 30, "seed": 42},
        ]
        
        run_tournament(configs, args.tournament_dir)
        
    else:
        # Single simulation
        config = {
            "num_snakes": args.agents,
            "grid_size": args.grid_size,
            "duration": args.duration,
            "target_fps": args.fps,
            "seed": args.seed,
        }
        
        simulation = HeadlessSimulation(config)
        stats = simulation.run()
        simulation.save_stats(args.output)
        
        # Print summary
        print("\\n=== Simulation Summary ===")
        print(f"Duration: {stats['duration']:.1f}s")
        print(f"Average FPS: {stats['performance'].get('average_fps', 0):.1f}")
        print(f"Final alive snakes: {stats['final_state']['alive_snakes']}")
        print(f"Total food eaten: {stats['final_state']['total_food_eaten']}")


if __name__ == "__main__":
    main()
