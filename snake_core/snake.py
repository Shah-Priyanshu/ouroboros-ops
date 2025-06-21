"""Snake state machine and behavior logic."""

from enum import IntEnum
from typing import List, Tuple, Optional, Deque, Dict, Any
from collections import deque
from numba import njit

from .grid import Grid, DIRECTIONS, EAST


class SnakeState(IntEnum):
    """Snake state enumeration."""
    ALIVE = 0
    DEAD = 1
    GROWING = 2
    DYING = 3  # Death animation state


@njit(cache=True)
def get_opposite_direction(direction: int) -> int:
    """Get opposite direction to prevent self-collision."""
    return (direction + 2) % 4


class Snake:
    """High-performance snake with cached pathfinding and state management.
    
    Each snake maintains its own body segments, current direction, and growth state.
    Uses deque for O(1) head/tail operations during movement.
    """
    
    def __init__(self, snake_id: int, start_row: int, start_col: int, 
                 initial_length: int = 3, initial_direction: int = EAST):
        """Initialize snake at starting position.
        
        Args:
            snake_id: Unique identifier for this snake
            start_row: Starting row position
            start_col: Starting column position            initial_length: Initial body length (minimum 2)
            initial_direction: Initial movement direction
        """
        self.snake_id = snake_id
        self.state = SnakeState.ALIVE
        self.direction = initial_direction
        self.length = max(2, initial_length)
        self.growth_pending = 0
        
        # Death animation tracking
        self.death_time = 0.0
        self.death_duration = 5.0  # 5 seconds death animation
        
        # Initialize body segments - head at front, tail at back
        self.body: Deque[Tuple[int, int]] = deque()
          # Create initial body extending backwards from head
        dr, dc = DIRECTIONS[get_opposite_direction(initial_direction)]
        for i in range(self.length):
            row = start_row + i * dr
            col = start_col + i * dc
            self.body.append((row, col))
            
        # Pathfinding cache
        self.cached_path: List[Tuple[int, int]] = []
        self.path_target: Optional[Tuple[int, int]] = None
        self.path_valid = False
        
        # Performance metrics
        self.moves_made = 0
        self.food_eaten = 0
        self.last_move_time = 0.0
        
    def get_head_position(self) -> Tuple[int, int]:
        """Get current head position."""
        return self.body[0]
        
    def get_tail_position(self) -> Tuple[int, int]:
        """Get current tail position."""
        return self.body[-1]
        
    def get_next_head_position(self) -> Tuple[int, int]:
        """Calculate next head position based on current direction."""
        head_row, head_col = self.get_head_position()
        dr, dc = DIRECTIONS[self.direction]
        return head_row + dr, head_col + dc
        
    def can_turn(self, new_direction: int) -> bool:
        """Check if snake can turn to new direction (no 180-degree turns)."""
        if self.state != SnakeState.ALIVE:
            return False
        return new_direction != get_opposite_direction(self.direction)
        
    def set_direction(self, new_direction: int) -> bool:
        """Set new movement direction if valid.
        
        Args:
            new_direction: New direction (NORTH, EAST, SOUTH, WEST)
            
        Returns:
            True if direction was changed, False if invalid
        """
        if self.can_turn(new_direction):
            self.direction = new_direction
            return True
        return False
        
    def move(self, grid: Grid, ate_food: bool = False) -> bool:
        """Move snake forward and update grid.
        
        Args:
            grid: Game grid to update
            ate_food: Whether food was consumed this move
            
        Returns:
            True if move was successful, False if snake died
        """
        if self.state != SnakeState.ALIVE:
            return False
            
        # Calculate new head position
        new_head = self.get_next_head_position()
        new_head_row, new_head_col = new_head
          # Check bounds
        if not (0 <= new_head_row < grid.height and 0 <= new_head_col < grid.width):
            self.die(grid)
            return False
            
        # Check collision with snakes (including self)
        if grid.has_snake(new_head_row, new_head_col):
            self.die(grid)
            return False
            
        # Clear old tail position if not growing
        old_tail = None
        if ate_food or self.growth_pending > 0:
            # Growing - don't remove tail
            if ate_food:
                self.food_eaten += 1
                self.growth_pending += 1
            if self.growth_pending > 0:
                self.growth_pending -= 1
                self.length += 1
                self.state = SnakeState.GROWING
        else:
            # Not growing - remove tail
            old_tail = self.body.pop()
            grid.clear_cell(old_tail[0], old_tail[1])
              # Add new head
        self.body.appendleft(new_head)
        
        # Update grid
        grid.set_snake_head(new_head_row, new_head_col)
        
        # Convert old head to body
        if len(self.body) > 1:
            old_head_row, old_head_col = self.body[1]
            grid.remove_snake_head(old_head_row, old_head_col)
            grid.set_snake_body(old_head_row, old_head_col)
            
        self.moves_made += 1
        self.state = SnakeState.ALIVE
        return True
        
    def die(self, grid: Grid) -> None:
        """Start death animation for snake."""
        import time
        self.state = SnakeState.DYING
        self.death_time = time.time()        # Clear snake from grid immediately to prevent collisions with dead body
        for row, col in self.body:
            grid.clear_cell(row, col)
        
    def update_death_animation(self, grid: Grid, current_time: float) -> bool:
        """Update death animation. Returns True if snake should be removed."""
        if self.state != SnakeState.DYING:
            return False
            
        if current_time - self.death_time >= self.death_duration:
            # Animation finished, mark as dead (grid already cleared in die())
            self.state = SnakeState.DEAD
            return True
            
        return False
        
    def is_dying(self) -> bool:
        """Check if snake is in death animation state."""
        return self.state == SnakeState.DYING
            
    def get_body_positions(self) -> List[Tuple[int, int]]:
        """Get all body segment positions."""
        return list(self.body)
        
    def invalidate_path_cache(self) -> None:
        """Invalidate cached pathfinding results."""
        self.path_valid = False
        self.cached_path.clear()
        self.path_target = None
        
    def set_cached_path(self, path: List[Tuple[int, int]], target: Tuple[int, int]) -> None:
        """Cache a computed path to target.
        
        Args:
            path: Sequence of positions from head to target
            target: Target position (usually food)
        """
        self.cached_path = path.copy()
        self.path_target = target
        self.path_valid = True
        
    def get_next_path_move(self) -> Optional[int]:
        """Get next direction from cached path.
        
        Returns:
            Direction constant or None if no valid path
        """
        if not self.path_valid or len(self.cached_path) < 2:
            return None
            
        current_pos = self.get_head_position()
        next_pos = self.cached_path[1]  # Skip current position
        
        # Calculate direction from current to next position
        dr = next_pos[0] - current_pos[0]
        dc = next_pos[1] - current_pos[1]
        
        # Convert to direction constant
        for direction, (check_dr, check_dc) in enumerate(DIRECTIONS):
            if dr == check_dr and dc == check_dc:
                return direction
                
        return None
        
    def is_path_blocked(self, grid: Grid) -> bool:
        """Check if current cached path is blocked."""
        if not self.path_valid or len(self.cached_path) < 2:
            return True
            
        # Check if next position in path is still walkable
        next_pos = self.cached_path[1]
        return not grid.is_walkable(next_pos[0], next_pos[1])
        
    def get_stats(self) -> Dict[str, Any]:
        """Get snake performance statistics."""
        return {
            'snake_id': self.snake_id,
            'state': self.state.name,
            'length': self.length,
            'moves_made': self.moves_made,
            'food_eaten': self.food_eaten,
            'position': self.get_head_position(),
            'direction': self.direction,
            'path_valid': self.path_valid,
            'path_length': len(self.cached_path),
        }
        
    def __repr__(self) -> str:
        """String representation for debugging."""
        head = self.get_head_position()
        return (f"Snake({self.snake_id}, {self.state.name}, "
                f"len={self.length}, pos={head}, dir={self.direction})")
