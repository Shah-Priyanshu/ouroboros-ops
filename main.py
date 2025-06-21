"""Main entry point for Ouroboros Ops."""

import time
import random
import argparse
from typing import List

from snake_core import Grid, Snake, FoodManager, PathFinder, SectorManager
from snake_core.snake import SnakeState
from engine import GameLoop, EventBus
from ui_pygame import GameRenderer


class OuroborosOps:
    """Main game class orchestrating all components."""
    
    def __init__(self, grid_size: int = 256, num_snakes: int = 100, 
                 target_fps: int = 60, headless: bool = False,
                 window_width: int = 1024, window_height: int = 768,
                 fullscreen: bool = False):
        """Initialize Ouroboros Ops simulation.
        
        Args:
            grid_size: Grid dimensions (grid_size x grid_size)
            num_snakes: Number of snakes to spawn
            target_fps: Target frames per second
            headless: Run without UI for benchmarking
            window_width: Window width in pixels
            window_height: Window height in pixels
            fullscreen: Start in fullscreen mode
        """
        self.grid_size = grid_size
        self.num_snakes = num_snakes
        self.headless = headless
        self.window_width = window_width
        self.window_height = window_height
        self.fullscreen = fullscreen
        
        # Core components
        self.grid = Grid(grid_size, grid_size)
        self.sector_manager = SectorManager(grid_size, grid_size, sector_size=16)
        self.food_manager = FoodManager(target_food_count=grid_size * 2)
        self.pathfinder = PathFinder(self.grid_size, self.grid_size)
        
        # Game state
        self.snakes: List[Snake] = []
        self.alive_snakes = 0
        self.total_food_eaten = 0
        
        # Engine
        self.game_loop = GameLoop(target_fps=target_fps)
        self.event_bus = EventBus()
        # Renderer (if not headless)
        self.renderer = None
        if not headless:
            self.renderer = GameRenderer(
                grid_size, grid_size, 
                window_width=self.window_width, 
                window_height=self.window_height,
                fullscreen=self.fullscreen
            )
            
        # Setup callbacks
        self.game_loop.set_update_callback(self.update)
        if self.renderer:
            self.game_loop.set_render_callback(self.render)
        self.game_loop.set_stats_callback(self.on_frame_stats)
        
        # Statistics
        self.frame_count = 0
        self.last_stats_time = 0.0
        
    def initialize(self) -> None:
        """Initialize game state."""
        print(f"Initializing Ouroboros Ops: {self.grid_size}x{self.grid_size} grid, {self.num_snakes} snakes")
        
        # Spawn snakes first
        self.spawn_snakes()
        
        # Then spawn initial food (proportional to grid size, but leave room for snakes)
        total_cells = self.grid_size * self.grid_size
        # Use the target_food_count from FoodManager, but ensure it's reasonable
        food_count = min(self.food_manager.target_food_count, total_cells // 8)  # Max 12.5% of grid
        self.food_manager.spawn_food_batch(self.grid, food_count)
        
        print(f"Spawned {len(self.snakes)} snakes, {self.food_manager.get_current_food_count(self.grid)} food items")
        
    def spawn_snakes(self) -> None:
        """Spawn snakes at random positions."""
        empty_positions = self.grid.find_empty_cells()
        if len(empty_positions) < self.num_snakes:
            print(f"Warning: Only {len(empty_positions)} empty cells for {self.num_snakes} snakes")
        
        def is_valid_spawn_position(row: int, col: int, direction: int, length: int) -> bool:
            """Check if a snake can spawn at this position without going out of bounds."""
            from snake_core.snake import DIRECTIONS, get_opposite_direction
            dr, dc = DIRECTIONS[get_opposite_direction(direction)]
            
            for i in range(length):
                test_row = row + i * dr
                test_col = col + i * dc
                if (test_row < 0 or test_row >= self.grid_size or 
                    test_col < 0 or test_col >= self.grid_size or
                    not self.grid.is_empty(test_row, test_col)):
                    return False
            return True
            
        # Spawn snakes with simpler logic
        spawned_count = 0
        max_attempts = min(len(empty_positions) * 2, 1000)  # Reasonable limit
        attempts = 0
        
        while spawned_count < self.num_snakes and attempts < max_attempts and empty_positions:
            attempts += 1
            
            # Pick random position
            pos_idx = random.randint(0, len(empty_positions) - 1)
            start_row, start_col = empty_positions[pos_idx]
            
            # Try directions until we find a valid one
            directions = list(range(4))
            random.shuffle(directions)
            
            spawned = False
            for direction in directions:
                if is_valid_spawn_position(start_row, start_col, direction, 3):
                    # Create and place snake
                    snake = Snake(spawned_count, start_row, start_col, initial_length=3, initial_direction=direction)
                    
                    # Place snake on grid
                    for seg_row, seg_col in snake.get_body_positions():
                        if seg_row == snake.get_head_position()[0] and seg_col == snake.get_head_position()[1]:
                            self.grid.set_snake_head(seg_row, seg_col)
                        else:
                            self.grid.set_snake_body(seg_row, seg_col)
                    
                    self.snakes.append(snake)
                    spawned_count += 1
                    spawned = True
                    
                    # Remove used positions from empty_positions
                    for seg_row, seg_col in snake.get_body_positions():
                        if (seg_row, seg_col) in empty_positions:
                            empty_positions.remove((seg_row, seg_col))                    
                    break
            
            if not spawned:
                # This position didn't work, remove it
                empty_positions.pop(pos_idx)
        
        self.alive_snakes = len(self.snakes)
        print(f"Spawned {spawned_count} snakes, {len(self.snakes)} total")
        
        # Debug: Show first few snake positions
        for i, snake in enumerate(self.snakes[:3]):
            head_pos = snake.get_head_position()
            body_positions = list(snake.get_body_positions())
            print(f"  Snake {i}: head at {head_pos}, body: {body_positions}")
        
        if spawned_count < self.num_snakes:
            print(f"Could only spawn {spawned_count} out of {self.num_snakes} snakes after {attempts} attempts")
        
    def update(self, dt: float) -> None:
        """Update game state for one frame."""
        self.frame_count += 1
        
        # Update food spawning
        with self.game_loop.profiler.profile("food_update"):
            self.food_manager.update(self.grid)
            
        # AI decision phase (parallel in real implementation)
        with self.game_loop.profiler.profile("ai_decisions"):
            self.update_snake_ai()
              # Movement and collision phase
        with self.game_loop.profiler.profile("snake_movement"):
            self.update_snake_movement()
            
        # Clean up dead snakes
        with self.game_loop.profiler.profile("cleanup"):
            self.cleanup_dead_snakes()
            
        # Update death animations
        with self.game_loop.profiler.profile("death_animations"):
            self.update_death_animations()
            
        # Check if all snakes are dead - count actual alive snakes instead of relying on counter
        actual_alive_snakes = sum(1 for snake in self.snakes if snake.state.value == 0)  # ALIVE = 0
        actual_dying_snakes = sum(1 for snake in self.snakes if snake.state.value == 3)  # DYING = 3
        
        # Update counter if there's a mismatch
        if actual_alive_snakes != self.alive_snakes:
            self.alive_snakes = actual_alive_snakes
            
        # Check for game end condition (no alive snakes and no dying snakes)
        if actual_alive_snakes == 0 and actual_dying_snakes == 0 and len(self.snakes) > 0:
            print(f"\n🎯 All {len(self.snakes)} snakes have died! Game ending after {self.frame_count} frames...")
            self.game_loop.stop()
            return
            
        # Update sector manager
        # In real implementation, this would be called when grid changes
        if self.frame_count % 60 == 0:  # Every second
            self.sector_manager.clean_all_sectors()
            
    def update_snake_ai(self) -> None:
        """Update snake directions using simple A* pathfinding to food."""
        food_positions = self.food_manager.get_food_positions(self.grid)
        
        for snake in self.snakes:
            if snake.state == SnakeState.DEAD or snake.state == SnakeState.DYING:
                continue
                
            # Simple A* pathfinding approach
            head_row, head_col = snake.get_head_position()
            
            # Find path to nearest food
            path = self.pathfinder.find_path_to_food(self.grid, snake.snake_id, head_row, head_col, food_positions)
            
            if path and len(path) > 1:
                # Get direction to next step in path
                next_row, next_col = path[1]  # path[0] is current position
                dr, dc = next_row - head_row, next_col - head_col
                # Convert to direction
                from snake_core.grid import DIRECTIONS
                for direction, (check_dr, check_dc) in enumerate(DIRECTIONS):
                    if dr == check_dr and dc == check_dc:
                        if snake.can_turn(direction):
                            snake.set_direction(direction)
                        break
            else:
                # No path to food, move randomly in a safe direction
                from snake_core.grid import DIRECTIONS
                valid_directions = []
                for direction in range(4):
                    if snake.can_turn(direction):
                        # Check if this direction is safe (not immediately deadly)
                        dr, dc = DIRECTIONS[direction]
                        next_row, next_col = head_row + dr, head_col + dc
                        
                        # Check bounds and collisions
                        if (0 <= next_row < self.grid.height and 
                            0 <= next_col < self.grid.width and
                            not self.grid.has_snake(next_row, next_col)):
                            valid_directions.append(direction)                
                if valid_directions:
                    snake.set_direction(random.choice(valid_directions))
                    
    def update_snake_movement(self) -> None:
        """Update snake movement and handle collisions."""
        snakes_before = self.alive_snakes
        
        for i, snake in enumerate(self.snakes):
            if snake.state.value != 0:  # Not alive
                continue
                
            next_head = snake.get_next_head_position()
            next_row, next_col = next_head
            
            # Debug output for first few frames
            if self.frame_count <= 5:
                print(f"Frame {self.frame_count}: Snake {snake.snake_id} at {snake.get_head_position()} moving to {next_head}")
            
            # Check bounds using actual grid dimensions
            if (next_row < 0 or next_row >= self.grid.height or 
                next_col < 0 or next_col >= self.grid.width):
                # Snake hit boundary, kill it
                if self.frame_count <= 10:
                    print(f"  Snake {snake.snake_id} died: boundary collision at {next_head} (grid: {self.grid.width}x{self.grid.height})")
                snake.die(self.grid)
                self.alive_snakes -= 1
                continue
            
            # Check for food consumption
            ate_food = False
            if self.grid.has_food(next_row, next_col):
                ate_food = self.food_manager.consume_food(self.grid, next_row, next_col)
                if ate_food:
                    self.total_food_eaten += 1
                      # Move snake
            if not snake.move(self.grid, ate_food):
                # Snake died
                if self.frame_count <= 10:
                    print(f"  Snake {snake.snake_id} died: move() returned False at {next_head}")
                self.alive_snakes -= 1
                  # Debug output for snake deaths
        if snakes_before > self.alive_snakes and self.frame_count <= 10:
            print(f"  Lost {snakes_before - self.alive_snakes} snakes this frame ({snakes_before} -> {self.alive_snakes})")
                    
    def cleanup_dead_snakes(self) -> None:
        """Remove dead snakes from the game."""        
        # In a more optimized version, we'd use a different data structure
        # For now, just mark them as processed
        pass
        
    def update_death_animations(self) -> None:
        """Update death animations for all dying snakes."""
        import time
        current_time = time.time()
        
        # Remove dying snakes immediately from main list
        snakes_to_remove = []
        for i, snake in enumerate(self.snakes):
            if snake.state == SnakeState.DYING or snake.state == SnakeState.DEAD:
                # Remove immediately to prevent any interference
                snakes_to_remove.append(i)
                    
        # Remove dying/dead snakes (in reverse order) and update counter
        for i in reversed(snakes_to_remove):
            removed_snake = self.snakes[i]
            if removed_snake.state == SnakeState.DYING and self.alive_snakes > 0:
                self.alive_snakes -= 1
            del self.snakes[i]
            
    def render(self, interpolation: float) -> None:
        """Render the game state."""
        if self.renderer:
            self.renderer.render(self.grid, self.snakes, interpolation)
            # Check if renderer wants to quit
            if self.renderer.should_quit:
                self.game_loop.stop()
            
    def on_frame_stats(self, stats) -> None:
        """Handle frame statistics."""
        # Update stats with actual counts
        stats.snake_count = self.alive_snakes
        stats.food_count = self.food_manager.get_current_food_count(self.grid)
        
        # Print stats every second
        current_time = time.time()
        if current_time - self.last_stats_time >= 1.0:
            print(f"Frame {stats.frame_number}: {stats.fps:.1f} FPS, "
                  f"{self.alive_snakes} snakes, {stats.food_count} food, "
                  f"Update: {stats.update_time*1000:.1f}ms")
            self.last_stats_time = current_time
            
    def run(self) -> None:
        """Run the main game loop."""
        self.initialize()
        
        try:
            if self.renderer:
                self.renderer.initialize()
                
            self.game_loop.run()
            
        finally:
            if self.renderer:
                self.renderer.cleanup()
                
            # Print final statistics
            self.print_final_stats()
            
    def print_final_stats(self) -> None:
        """Print final performance statistics."""
        print("\n=== Final Statistics ===")
        print(f"Total frames: {self.frame_count}")
        print(f"Alive snakes: {self.alive_snakes}/{len(self.snakes)}")
        print(f"Total food eaten: {self.total_food_eaten}")
        
        # Game loop stats
        perf_stats = self.game_loop.get_performance_summary()
        print(f"Average FPS: {perf_stats.get('average_fps', 0):.1f}")
        
        # Profiler stats
        self.game_loop.profiler.print_summary()
        
        # Component stats
        print(f"\nFood Manager: {self.food_manager.get_stats()}")
        print(f"Pathfinder: {self.pathfinder.get_stats()}")
        print(f"Sector Manager: {self.sector_manager.get_stats()}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Ouroboros Ops - Massive Snake Battleground")
    parser.add_argument("--agents", type=int, default=100, help="Number of snakes")
    parser.add_argument("--grid-size", type=int, default=256, help="Grid size (NxN)")
    parser.add_argument("--fps", type=int, default=60, help="Target FPS")
    parser.add_argument("--headless", action="store_true", help="Run without UI")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--window-width", type=int, default=1024, help="Window width in pixels")
    parser.add_argument("--window-height", type=int, default=768, help="Window height in pixels")
    parser.add_argument("--fullscreen", action="store_true", help="Start in fullscreen mode")
    
    args = parser.parse_args()
    
    # Set random seed
    random.seed(args.seed)
    
    # Create and run game
    game = OuroborosOps(
        grid_size=args.grid_size,
        num_snakes=args.agents,
        target_fps=args.fps,
        headless=args.headless,
        window_width=args.window_width,
        window_height=args.window_height,
        fullscreen=args.fullscreen
    )
    
    game.run()


if __name__ == "__main__":
    main()
