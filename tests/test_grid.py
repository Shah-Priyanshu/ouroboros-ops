"""Tests for the core grid functionality."""

import pytest
import numpy as np
from snake_core import Grid, EMPTY, FOOD, SNAKE_BODY, SNAKE_HEAD


class TestGrid:
    """Test cases for Grid class."""
    
    def test_grid_initialization(self):
        """Test grid initialization."""
        grid = Grid(100, 100)
        assert grid.height == 100
        assert grid.width == 100
        assert grid.total_cells == 10000
        assert np.all(grid.grid == EMPTY)
        
    def test_cell_operations(self):
        """Test basic cell operations."""
        grid = Grid(10, 10)
        
        # Test empty checks
        assert grid.is_empty(5, 5)
        assert not grid.has_food(5, 5)
        assert not grid.has_snake(5, 5)
        
        # Test food operations
        grid.set_food(5, 5)
        assert grid.has_food(5, 5)
        assert not grid.is_empty(5, 5)
        
        grid.remove_food(5, 5)
        assert not grid.has_food(5, 5)
        assert grid.is_empty(5, 5)
        
        # Test snake operations
        grid.set_snake_head(3, 3)
        assert grid.has_snake_head(3, 3)
        assert grid.has_snake(3, 3)
        
        grid.set_snake_body(4, 4)
        assert grid.has_snake_body(4, 4)
        assert grid.has_snake(4, 4)
        
    def test_cell_combinations(self):
        """Test cells with multiple flags."""
        grid = Grid(10, 10)
        
        # Food + snake should not happen in practice, but test bit operations
        grid.set_food(5, 5)
        grid.set_snake_head(5, 5)
        
        assert grid.has_food(5, 5)
        assert grid.has_snake_head(5, 5)
        assert grid.has_snake(5, 5)
        
    def test_walkable_cells(self):
        """Test walkable cell detection."""
        grid = Grid(10, 10)
        
        # Empty cell is walkable
        assert grid.is_walkable(5, 5)
        
        # Food cell is walkable
        grid.set_food(5, 5)
        assert grid.is_walkable(5, 5)
        
        # Snake body is not walkable
        grid.clear_cell(5, 5)
        grid.set_snake_body(5, 5)
        assert not grid.is_walkable(5, 5)
        
        # Snake head is not walkable
        grid.clear_cell(5, 5)
        grid.set_snake_head(5, 5)
        assert not grid.is_walkable(5, 5)
        
        # Out of bounds is not walkable
        assert not grid.is_walkable(-1, 5)
        assert not grid.is_walkable(5, -1)
        assert not grid.is_walkable(10, 5)
        assert not grid.is_walkable(5, 10)
        
    def test_empty_cells_finding(self):
        """Test finding empty cells."""
        grid = Grid(5, 5)
        
        # All cells should be empty initially
        empty_cells = grid.find_empty_cells()
        assert len(empty_cells) == 25
        
        # Add some obstacles
        grid.set_food(2, 2)
        grid.set_snake_head(3, 3)
        grid.set_snake_body(4, 4)
        
        empty_cells = grid.find_empty_cells()
        assert len(empty_cells) == 22  # 25 - 3 occupied
        assert (2, 2) not in empty_cells
        assert (3, 3) not in empty_cells
        assert (4, 4) not in empty_cells
        
    def test_cell_counting(self):
        """Test cell type counting."""
        grid = Grid(10, 10)
        
        # Initially all empty
        empty, food, body, head = grid.count_cell_types()
        assert empty == 100
        assert food == 0
        assert body == 0
        assert head == 0
        
        # Add some entities
        grid.set_food(1, 1)
        grid.set_food(2, 2)
        grid.set_snake_head(5, 5)
        grid.set_snake_body(6, 6)
        grid.set_snake_body(7, 7)
        
        empty, food, body, head = grid.count_cell_types()
        assert empty == 95
        assert food == 2
        assert body == 2
        assert head == 1
        
    def test_grid_copy(self):
        """Test grid copying."""
        grid1 = Grid(5, 5)
        grid1.set_food(2, 2)
        grid1.set_snake_head(3, 3)
        
        grid2 = grid1.copy()
        
        # Should be independent
        assert np.array_equal(grid1.grid, grid2.grid)
        
        # Modify original        grid1.set_food(4, 4)
        
        # Copy should be unchanged
        assert not np.array_equal(grid1.grid, grid2.grid)
        assert not grid2.has_food(4, 4)
        
    def test_density_map(self):
        """Test density map generation."""
        grid = Grid(5, 5)
        
        grid.set_food(1, 1)
        grid.set_snake_body(2, 2)  
        grid.set_snake_head(3, 3)
        
        density = grid.get_density_map()
        
        assert density[0, 0] == pytest.approx(0.0)  # Empty
        assert density[1, 1] == pytest.approx(0.3)  # Food
        assert density[2, 2] == pytest.approx(0.7)  # Snake body
        assert density[3, 3] == pytest.approx(1.0)  # Snake head


if __name__ == "__main__":
    pytest.main([__file__])
