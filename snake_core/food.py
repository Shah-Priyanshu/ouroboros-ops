"""Food spawning and management with vectorized RNG operations."""

import numpy as np
from typing import List, Tuple, Set
from numba import njit

from .grid import Grid


@njit(cache=True)
def fast_random_choice(empty_indices: np.ndarray, count: int, rng_state: np.ndarray) -> np.ndarray:
    """Fast random selection of indices using Numba-compatible RNG."""
    n_empty = len(empty_indices)
    if count >= n_empty:
        return empty_indices
    
    # Simple linear congruential generator for speed
    selected = np.empty(count, dtype=np.int32)
    for i in range(count):
        rng_state[0] = (rng_state[0] * 1103515245 + 12345) & 0x7fffffff
        idx = rng_state[0] % n_empty
        selected[i] = empty_indices[idx]
        
        # Swap selected element to end to avoid reselection
        empty_indices[idx], empty_indices[n_empty - 1] = empty_indices[n_empty - 1], empty_indices[idx]
        n_empty -= 1
        
    return selected


class FoodManager:
    """Manages food spawning with optimized batch operations.
    
    Uses vectorized numpy operations for efficient food placement and
    maintains target food density across the grid.
    """
    
    def __init__(self, target_food_count: int = 1000, spawn_rate: float = 0.1,
                 max_food_per_spawn: int = 50, seed: int = 42):
        """Initialize food manager.
        
        Args:
            target_food_count: Target number of food items to maintain
            spawn_rate: Probability of spawning food each frame  
            max_food_per_spawn: Maximum food items to spawn per frame
            seed: Random seed for reproducible behavior
        """
        self.target_food_count = target_food_count
        self.spawn_rate = spawn_rate
        self.max_food_per_spawn = max_food_per_spawn
        
        # RNG state for Numba compatibility
        self.rng_state = np.array([seed], dtype=np.uint32)
        
        # Statistics
        self.total_spawned = 0
        self.total_consumed = 0
        self.spawn_attempts = 0
        
        # Cache for empty positions to avoid frequent recalculation
        self._empty_positions_cache: List[Tuple[int, int]] = []
        self._cache_valid = False
        
    def update_cache(self, grid: Grid) -> None:
        """Update cache of empty positions."""
        self._empty_positions_cache = grid.find_empty_cells()
        self._cache_valid = True
        
    def invalidate_cache(self) -> None:
        """Invalidate position cache after grid changes."""
        self._cache_valid = False
        
    def get_current_food_count(self, grid: Grid) -> int:
        """Count current food items on grid."""
        return int(np.sum(grid.grid & 1 > 0))  # Count FOOD flag
        
    def should_spawn_food(self, grid: Grid) -> bool:
        """Determine if food should be spawned this frame."""
        current_count = self.get_current_food_count(grid)
        
        if current_count >= self.target_food_count:
            return False
            
        # Increase spawn probability when food is scarce
        scarcity_factor = 1.0 - (current_count / self.target_food_count)
        effective_rate = self.spawn_rate * (1.0 + scarcity_factor)
        
        # Simple RNG check
        self.rng_state[0] = (self.rng_state[0] * 1103515245 + 12345) & 0x7fffffff
        return (self.rng_state[0] / 0x7fffffff) < effective_rate
        
    def spawn_food_batch(self, grid: Grid, count: int) -> int:
        """Spawn multiple food items efficiently.
        
        Args:
            grid: Game grid to spawn food on
            count: Number of food items to spawn
            
        Returns:
            Number of food items actually spawned
        """
        if not self._cache_valid:
            self.update_cache(grid)
            
        if not self._empty_positions_cache:
            return 0
            
        # Limit spawn count to available positions
        spawn_count = min(count, len(self._empty_positions_cache))
        if spawn_count <= 0:
            return 0
            
        # Convert positions to indices for fast selection
        empty_indices = np.arange(len(self._empty_positions_cache), dtype=np.int32)
        
        # Select random positions
        selected_indices = fast_random_choice(empty_indices, spawn_count, self.rng_state)
        
        # Place food at selected positions
        spawned = 0
        for idx in selected_indices:
            if idx < len(self._empty_positions_cache):
                row, col = self._empty_positions_cache[idx]
                if grid.is_empty(row, col):  # Double-check emptiness
                    grid.set_food(row, col)
                    spawned += 1
                    
        self.total_spawned += spawned
        self.invalidate_cache()  # Cache is now stale
        return spawned
        
    def update(self, grid: Grid) -> int:
        """Update food spawning for current frame.
        
        Args:
            grid: Game grid to update
            
        Returns:
            Number of food items spawned
        """
        self.spawn_attempts += 1
        
        if not self.should_spawn_food(grid):
            return 0
            
        current_count = self.get_current_food_count(grid)
        deficit = max(0, self.target_food_count - current_count)
        
        # Spawn up to the deficit, but not more than max per spawn
        spawn_count = min(deficit, self.max_food_per_spawn)
        
        return self.spawn_food_batch(grid, spawn_count)
        
    def consume_food(self, grid: Grid, row: int, col: int) -> bool:
        """Consume food at position if present.
        
        Args:
            grid: Game grid
            row: Food row position
            col: Food column position
            
        Returns:
            True if food was consumed, False if no food present
        """
        if grid.has_food(row, col):
            grid.remove_food(row, col)
            self.total_consumed += 1
            self.invalidate_cache()
            return True
        return False
        
    def get_food_positions(self, grid: Grid) -> List[Tuple[int, int]]:
        """Get all current food positions."""
        positions = []
        rows, cols = np.where(grid.grid & 1 > 0)  # Find FOOD flag
        for r, c in zip(rows, cols):
            positions.append((int(r), int(c)))
        return positions
        
    def find_nearest_food(self, grid: Grid, from_row: int, from_col: int) -> Tuple[int, int, float]:
        """Find nearest food using Manhattan distance.
        
        Args:
            grid: Game grid
            from_row: Starting row
            from_col: Starting column
            
        Returns:
            Tuple of (food_row, food_col, distance) or (-1, -1, float('inf')) if no food
        """
        food_positions = self.get_food_positions(grid)
        
        if not food_positions:
            return -1, -1, float('inf')
            
        min_distance = float('inf')
        nearest_food = (-1, -1)
        
        for food_row, food_col in food_positions:
            # Manhattan distance
            distance = abs(food_row - from_row) + abs(food_col - from_col)
            if distance < min_distance:
                min_distance = distance
                nearest_food = (food_row, food_col)
                
        return nearest_food[0], nearest_food[1], min_distance
        
    def get_food_density(self, grid: Grid) -> float:
        """Calculate current food density (0.0 to 1.0)."""
        current_count = self.get_current_food_count(grid)
        return current_count / grid.total_cells
        
    def reset_stats(self) -> None:
        """Reset food statistics."""
        self.total_spawned = 0
        self.total_consumed = 0
        self.spawn_attempts = 0
        
    def get_stats(self) -> dict:
        """Get food management statistics."""
        return {
            'target_food_count': self.target_food_count,
            'total_spawned': self.total_spawned,
            'total_consumed': self.total_consumed,
            'spawn_attempts': self.spawn_attempts,
            'spawn_rate': self.spawn_rate,
            'cache_valid': self._cache_valid,
            'cached_positions': len(self._empty_positions_cache),
        }
        
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"FoodManager(target={self.target_food_count}, "
                f"spawned={self.total_spawned}, consumed={self.total_consumed})")
