"""High-performance grid representation using numpy arrays with bit-encoded cells."""

import numpy as np
from typing import Tuple, List, Optional
from numba import njit, types
from numba.typed import List as NumbaList

# Cell type constants - bit flags for efficient storage
EMPTY = 0
FOOD = 1
SNAKE_BODY = 2
SNAKE_HEAD = 4

# Direction constants
NORTH = 0
EAST = 1  
SOUTH = 2
WEST = 3

# Direction vectors for fast lookup
DIRECTIONS = np.array([
    [-1, 0],  # NORTH
    [0, 1],   # EAST  
    [1, 0],   # SOUTH
    [0, -1]   # WEST
], dtype=np.int16)


@njit(cache=True)
def is_valid_position(row: int, col: int, height: int, width: int) -> bool:
    """Check if position is within grid bounds."""
    return 0 <= row < height and 0 <= col < width


@njit(cache=True)
def get_neighbors(row: int, col: int, height: int, width: int) -> types.List:
    """Get valid neighboring positions."""
    neighbors = NumbaList.empty_list(types.UniTuple(types.int16, 2))
    
    for i in range(4):
        dr, dc = DIRECTIONS[i]
        new_row, new_col = row + dr, col + dc
        
        if is_valid_position(new_row, new_col, height, width):
            neighbors.append((new_row, new_col))
    
    return neighbors


class Grid:
    """Numpy-backed grid with bit-encoded cell flags for maximum performance.
    
    Uses uint16 for each cell with bit flags:
    - Bit 0: FOOD (1)
    - Bit 1: SNAKE_BODY (2) 
    - Bit 2: SNAKE_HEAD (4)
    
    This allows for O(1) collision detection and efficient SIMD operations.
    """
    
    def __init__(self, height: int = 256, width: int = 256):
        """Initialize grid with specified dimensions.
        
        Args:
            height: Grid height (default 256)
            width: Grid width (default 256)
        """
        self.height = height
        self.width = width
        self.grid = np.zeros((height, width), dtype=np.uint16)
        self.total_cells = height * width
        
    def clear(self) -> None:
        """Clear entire grid to empty state."""
        self.grid.fill(EMPTY)
        
    def is_empty(self, row: int, col: int) -> bool:
        """Check if cell is completely empty."""
        return self.grid[row, col] == EMPTY
        
    def has_food(self, row: int, col: int) -> bool:
        """Check if cell contains food."""
        return bool(self.grid[row, col] & FOOD)
        
    def has_snake(self, row: int, col: int) -> bool:
        """Check if cell contains any snake part."""
        return bool(self.grid[row, col] & (SNAKE_BODY | SNAKE_HEAD))
        
    def has_snake_head(self, row: int, col: int) -> bool:
        """Check if cell contains snake head."""
        return bool(self.grid[row, col] & SNAKE_HEAD)
        
    def has_snake_body(self, row: int, col: int) -> bool:
        """Check if cell contains snake body."""
        return bool(self.grid[row, col] & SNAKE_BODY)
        
    def set_food(self, row: int, col: int) -> None:
        """Place food at position."""
        self.grid[row, col] |= FOOD
        
    def remove_food(self, row: int, col: int) -> None:
        """Remove food from position."""
        self.grid[row, col] &= ~FOOD
        
    def set_snake_head(self, row: int, col: int) -> None:
        """Place snake head at position."""
        self.grid[row, col] |= SNAKE_HEAD
        
    def set_snake_body(self, row: int, col: int) -> None:
        """Place snake body at position.""" 
        self.grid[row, col] |= SNAKE_BODY
        
    def remove_snake_head(self, row: int, col: int) -> None:
        """Remove snake head from position."""
        self.grid[row, col] &= ~SNAKE_HEAD
        
    def remove_snake_body(self, row: int, col: int) -> None:
        """Remove snake body from position."""
        self.grid[row, col] &= ~SNAKE_BODY
        
    def clear_cell(self, row: int, col: int) -> None:
        """Clear all flags from cell."""
        self.grid[row, col] = EMPTY
        
    def get_cell_type(self, row: int, col: int) -> int:
        """Get the cell type value."""
        return self.grid[row, col]
        
    def is_walkable(self, row: int, col: int) -> bool:
        """Check if cell is walkable (empty or contains only food)."""
        if not is_valid_position(row, col, self.height, self.width):
            return False
        return not self.has_snake(row, col)
        
    def find_empty_cells(self) -> List[Tuple[int, int]]:
        """Find all empty cells for food spawning."""
        empty_positions = []
        rows, cols = np.where(self.grid == EMPTY)
        for r, c in zip(rows, cols):
            empty_positions.append((int(r), int(c)))
        return empty_positions
        
    def count_cell_types(self) -> Tuple[int, int, int, int]:
        """Count cells by type: (empty, food, snake_body, snake_head)."""
        empty = np.sum(self.grid == EMPTY)
        food = np.sum(self.grid & FOOD > 0) 
        snake_body = np.sum(self.grid & SNAKE_BODY > 0)
        snake_head = np.sum(self.grid & SNAKE_HEAD > 0)
        return int(empty), int(food), int(snake_body), int(snake_head)
        
    def get_density_map(self) -> np.ndarray:
        """Get density map for visualization (0-1 normalized)."""
        # Convert bit flags to density values
        density = np.zeros_like(self.grid, dtype=np.float32)
        density[self.grid & FOOD > 0] = 0.3
        density[self.grid & SNAKE_BODY > 0] = 0.7  
        density[self.grid & SNAKE_HEAD > 0] = 1.0
        return density
        
    def copy(self) -> 'Grid':
        """Create a deep copy of the grid."""
        new_grid = Grid(self.height, self.width)
        new_grid.grid = self.grid.copy()
        return new_grid
        
    def __repr__(self) -> str:
        """String representation for debugging."""
        empty, food, body, head = self.count_cell_types()
        return (f"Grid({self.height}x{self.width}, "
                f"empty={empty}, food={food}, body={body}, head={head})")
