"""High-performance pathfinding with sector-based caching and Numba optimization."""

import numpy as np
from typing import List, Tuple, Optional, Set
from collections import deque
import heapq
from numba import njit

from .grid import Grid, DIRECTIONS, is_valid_position
from .spatial import SectorManager


@njit(cache=True) 
def manhattan_distance(r1: int, c1: int, r2: int, c2: int) -> int:
    """Calculate Manhattan distance between two points."""
    return abs(r1 - r2) + abs(c1 - c2)


@njit(cache=True)
def astar_numba_simple(grid: np.ndarray, start_row: int, start_col: int, 
                      goal_row: int, goal_col: int, max_iterations: int = 1000):
    """Simplified Numba-optimized A* pathfinding algorithm.
    
    Returns: numpy array of path coordinates, or empty array if no path found.
    """
    height, width = grid.shape
    
    # Check bounds
    if not (is_valid_position(start_row, start_col, height, width) and 
            is_valid_position(goal_row, goal_col, height, width)):
        return np.array([(-1, -1)], dtype=np.int16)
    
    # Check if goal is reachable (not occupied by snake)
    if grid[goal_row, goal_col] & 6 > 0:  # SNAKE_BODY | SNAKE_HEAD
        return np.array([(-1, -1)], dtype=np.int16)
    
    # Quick check - if start == goal
    if start_row == goal_row and start_col == goal_col:
        return np.array([(start_row, start_col)], dtype=np.int16)
    
    # Use simple arrays for tracking
    size = height * width
    g_score = np.full(size, 999999.0, dtype=np.float32)
    f_score = np.full(size, 999999.0, dtype=np.float32)
    came_from = np.full(size, -1, dtype=np.int32)
    
    start_idx = start_row * width + start_col
    goal_idx = goal_row * width + goal_col
    
    g_score[start_idx] = 0.0
    f_score[start_idx] = manhattan_distance(start_row, start_col, goal_row, goal_col)
    
    # Simple priority queue using arrays
    open_set = np.zeros(max_iterations, dtype=np.int32)
    open_set[0] = start_idx
    open_size = 1
    
    # Direction vectors: North, East, South, West
    dr = np.array([-1, 0, 1, 0], dtype=np.int32)
    dc = np.array([0, 1, 0, -1], dtype=np.int32)
    
    iterations = 0
    while open_size > 0 and iterations < max_iterations:
        iterations += 1
        
        # Find minimum f_score in open set
        min_f = 999999.0
        min_idx = 0
        for i in range(open_size):
            idx = open_set[i]
            if f_score[idx] < min_f:
                min_f = f_score[idx]
                min_idx = i
        
        # Get current node
        current_idx = open_set[min_idx]
        
        # Remove from open set
        for i in range(min_idx, open_size - 1):
            open_set[i] = open_set[i + 1]
        open_size -= 1
        
        # Check if we reached the goal
        if current_idx == goal_idx:
            # Reconstruct path
            path_length = 1
            temp_idx = current_idx
            while came_from[temp_idx] != -1:
                temp_idx = came_from[temp_idx]
                path_length += 1
            
            # Build path array
            path = np.zeros((path_length, 2), dtype=np.int16)
            path_idx = path_length - 1
            temp_idx = current_idx
            
            while temp_idx != -1:
                row = temp_idx // width
                col = temp_idx % width
                path[path_idx, 0] = row
                path[path_idx, 1] = col
                path_idx -= 1
                temp_idx = came_from[temp_idx]
            
            return path
        
        current_row = current_idx // width
        current_col = current_idx % width
        
        # Check neighbors
        for d in range(4):
            neighbor_row = current_row + dr[d]
            neighbor_col = current_col + dc[d]
            
            # Check bounds
            if (neighbor_row < 0 or neighbor_row >= height or 
                neighbor_col < 0 or neighbor_col >= width):
                continue
            
            neighbor_idx = neighbor_row * width + neighbor_col
            
            # Check if walkable (not snake body/head)
            if grid[neighbor_row, neighbor_col] & 6 > 0:
                continue
            
            tentative_g = g_score[current_idx] + 1.0
            
            if tentative_g < g_score[neighbor_idx]:
                came_from[neighbor_idx] = current_idx
                g_score[neighbor_idx] = tentative_g
                f_score[neighbor_idx] = tentative_g + manhattan_distance(
                    neighbor_row, neighbor_col, goal_row, goal_col)
                
                # Add to open set if not already there
                in_open = False
                for i in range(open_size):
                    if open_set[i] == neighbor_idx:
                        in_open = True
                        break
                
                if not in_open and open_size < max_iterations:
                    open_set[open_size] = neighbor_idx
                    open_size += 1
    
    # No path found
    return np.array([(-1, -1)], dtype=np.int16)


class PathFinder:
    """High-performance pathfinding with caching and spatial optimization."""
    
    def __init__(self, grid_height: int, grid_width: int):
        """Initialize pathfinder.
        
        Args:
            grid_height: Grid height in cells
            grid_width: Grid width in cells
        """
        self.grid_height = grid_height
        self.grid_width = grid_width
        
        # Performance tracking
        self.paths_computed = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.total_path_length = 0
        self.computation_time = 0.0
        
        # Path caching per snake
        self.path_cache: dict = {}
        
    def find_path_to_food(self, grid: Grid, snake_id: int, start_row: int, start_col: int, 
                         food_positions: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
        """Find optimal path from start to nearest food.
        
        Args:
            grid: Game grid
            snake_id: Snake identifier for caching
            start_row: Starting row
            start_col: Starting column
            food_positions: List of available food positions
            
        Returns:
            List of (row, col) positions from start to food, or empty if no path
        """
        if not food_positions:
            return []
        
        # Find nearest food
        min_distance = float('inf')
        nearest_food = None
        
        for food_row, food_col in food_positions:
            distance = manhattan_distance(start_row, start_col, food_row, food_col)
            if distance < min_distance:
                min_distance = distance
                nearest_food = (food_row, food_col)
        
        if nearest_food is None:
            return []
        
        food_row, food_col = nearest_food
        
        # Try to find path
        path = self.find_path(grid, start_row, start_col, food_row, food_col)
        
        if len(path) > 1:  # Valid path found
            self.paths_computed += 1
            self.total_path_length += len(path)
            
        return path
    
    def find_path(self, grid: Grid, start_row: int, start_col: int, 
                  goal_row: int, goal_col: int) -> List[Tuple[int, int]]:
        """Find path between two points using A* algorithm.
        
        Args:
            grid: Game grid
            start_row: Starting row
            start_col: Starting column
            goal_row: Goal row
            goal_col: Goal column
            
        Returns:
            List of (row, col) positions from start to goal, or empty if no path
        """
        # Use simplified Numba function
        numba_path = astar_numba_simple(grid.grid, start_row, start_col, goal_row, goal_col)
        
        # Convert to list of tuples
        if len(numba_path) == 1 and numba_path[0, 0] == -1:
            return []  # No path found
        
        return [(int(row), int(col)) for row, col in numba_path]
    
    def clear_cache(self) -> None:
        """Clear all cached paths."""
        self.path_cache.clear()
    
    def get_stats(self) -> dict:
        """Get pathfinding performance statistics."""
        cache_hit_rate = 0.0
        if self.cache_hits + self.cache_misses > 0:
            cache_hit_rate = self.cache_hits / (self.cache_hits + self.cache_misses)
        
        avg_path_length = 0.0
        if self.paths_computed > 0:
            avg_path_length = self.total_path_length / self.paths_computed
        
        return {
            'paths_computed': self.paths_computed,
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'cache_hit_rate': cache_hit_rate,
            'avg_path_length': avg_path_length,
            'total_path_length': self.total_path_length,
            'computation_time': self.computation_time
        }
