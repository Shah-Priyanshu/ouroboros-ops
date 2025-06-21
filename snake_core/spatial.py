"""Spatial partitioning system for efficient sector-based operations."""

import numpy as np
from typing import List, Tuple, Set, Dict, Any
from numba import njit


@njit(cache=True)
def get_sector_coords(row: int, col: int, sector_size: int) -> Tuple[int, int]:
    """Get sector coordinates for a given position."""
    return row // sector_size, col // sector_size


@njit(cache=True)
def get_sectors_in_region(min_row: int, min_col: int, max_row: int, max_col: int, 
                         sector_size: int) -> List[Tuple[int, int]]:
    """Get all sectors that overlap with a rectangular region."""
    sectors = []
    
    min_sector_row = min_row // sector_size
    min_sector_col = min_col // sector_size
    max_sector_row = max_row // sector_size  
    max_sector_col = max_col // sector_size
    
    for sr in range(min_sector_row, max_sector_row + 1):
        for sc in range(min_sector_col, max_sector_col + 1):
            sectors.append((sr, sc))
            
    return sectors


class SectorManager:
    """Manages spatial partitioning into sectors for optimized pathfinding.
    
    Divides the grid into fixed-size sectors and tracks which sectors
    have been modified (dirty) to minimize pathfinding recalculations.
    """
    
    def __init__(self, grid_height: int, grid_width: int, sector_size: int = 16):
        """Initialize sector manager.
        
        Args:
            grid_height: Total grid height
            grid_width: Total grid width  
            sector_size: Size of each sector (default 16x16)
        """
        self.grid_height = grid_height
        self.grid_width = grid_width
        self.sector_size = sector_size
        
        # Calculate sector grid dimensions
        self.sectors_high = (grid_height + sector_size - 1) // sector_size
        self.sectors_wide = (grid_width + sector_size - 1) // sector_size
        
        # Dirty flags for each sector
        self.dirty_sectors: Set[Tuple[int, int]] = set()
        
        # Statistics
        self.total_sectors = self.sectors_high * self.sectors_wide
        self.dirty_count = 0
        self.clean_operations = 0
        
    def get_sector(self, row: int, col: int) -> Tuple[int, int]:
        """Get sector coordinates for a position.
        
        Args:
            row: Grid row
            col: Grid column
            
        Returns:
            Tuple of (sector_row, sector_col)
        """
        return get_sector_coords(row, col, self.sector_size)
        
    def mark_dirty(self, row: int, col: int) -> None:
        """Mark sector containing position as dirty.
        
        Args:
            row: Grid row that changed
            col: Grid column that changed
        """
        sector = self.get_sector(row, col)
        if sector not in self.dirty_sectors:
            self.dirty_sectors.add(sector)
            self.dirty_count += 1
            
    def mark_region_dirty(self, min_row: int, min_col: int, 
                         max_row: int, max_col: int) -> None:
        """Mark all sectors overlapping a region as dirty.
        
        Args:
            min_row: Minimum row of region
            min_col: Minimum column of region
            max_row: Maximum row of region
            max_col: Maximum column of region
        """
        sectors = get_sectors_in_region(min_row, min_col, max_row, max_col, self.sector_size)
        
        for sector in sectors:
            if sector not in self.dirty_sectors:
                self.dirty_sectors.add(sector)
                self.dirty_count += 1
                
    def is_sector_dirty(self, sector_row: int, sector_col: int) -> bool:
        """Check if a sector is marked as dirty.
        
        Args:
            sector_row: Sector row coordinate
            sector_col: Sector column coordinate
            
        Returns:
            True if sector is dirty
        """
        return (sector_row, sector_col) in self.dirty_sectors
        
    def is_position_in_dirty_sector(self, row: int, col: int) -> bool:
        """Check if position is in a dirty sector.
        
        Args:
            row: Grid row
            col: Grid column
            
        Returns:
            True if position's sector is dirty
        """
        sector = self.get_sector(row, col)
        return sector in self.dirty_sectors
        
    def clean_sector(self, sector_row: int, sector_col: int) -> None:
        """Mark sector as clean (no longer dirty).
        
        Args:
            sector_row: Sector row coordinate
            sector_col: Sector column coordinate
        """
        sector = (sector_row, sector_col)
        if sector in self.dirty_sectors:
            self.dirty_sectors.remove(sector)
            self.clean_operations += 1
            
    def clean_all_sectors(self) -> None:
        """Mark all sectors as clean."""
        cleaned_count = len(self.dirty_sectors)
        self.dirty_sectors.clear()
        self.clean_operations += cleaned_count
        
    def get_dirty_sectors(self) -> List[Tuple[int, int]]:
        """Get list of all dirty sectors.
        
        Returns:
            List of (sector_row, sector_col) tuples
        """
        return list(self.dirty_sectors)
        
    def get_sectors_for_path(self, start_row: int, start_col: int, 
                           end_row: int, end_col: int) -> List[Tuple[int, int]]:
        """Get all sectors that a path between two points might traverse.
        
        Args:
            start_row: Path start row
            start_col: Path start column
            end_row: Path end row  
            end_col: Path end column
            
        Returns:
            List of sector coordinates the path might cross
        """
        return get_sectors_in_region(
            min(start_row, end_row), min(start_col, end_col),
            max(start_row, end_row), max(start_col, end_col),
            self.sector_size
        )
        
    def should_recompute_path(self, start_row: int, start_col: int,
                            end_row: int, end_col: int) -> bool:
        """Check if path should be recomputed based on dirty sectors.
        
        Args:
            start_row: Path start row
            start_col: Path start column
            end_row: Path end row
            end_col: Path end column
            
        Returns:
            True if any sector along path is dirty
        """
        path_sectors = self.get_sectors_for_path(start_row, start_col, end_row, end_col)
        
        for sector in path_sectors:
            if sector in self.dirty_sectors:
                return True
                
        return False
        
    def get_sector_bounds(self, sector_row: int, sector_col: int) -> Tuple[int, int, int, int]:
        """Get grid bounds for a sector.
        
        Args:
            sector_row: Sector row coordinate
            sector_col: Sector column coordinate
            
        Returns:
            Tuple of (min_row, min_col, max_row, max_col)
        """
        min_row = sector_row * self.sector_size
        min_col = sector_col * self.sector_size
        max_row = min(min_row + self.sector_size - 1, self.grid_height - 1)
        max_col = min(min_col + self.sector_size - 1, self.grid_width - 1)
        
        return min_row, min_col, max_row, max_col
        
    def get_neighboring_sectors(self, sector_row: int, sector_col: int) -> List[Tuple[int, int]]:
        """Get all neighboring sectors (8-connected).
        
        Args:
            sector_row: Sector row coordinate
            sector_col: Sector column coordinate
            
        Returns:
            List of neighboring sector coordinates
        """
        neighbors = []
        
        for dr in [-1, 0, 1]:
            for dc in [-1, 0, 1]:
                if dr == 0 and dc == 0:
                    continue
                    
                nr = sector_row + dr
                nc = sector_col + dc
                
                if 0 <= nr < self.sectors_high and 0 <= nc < self.sectors_wide:
                    neighbors.append((nr, nc))
                    
        return neighbors
        
    def get_density_map(self) -> np.ndarray:
        """Get density map showing dirty sectors.
        
        Returns:
            2D array with 1.0 for dirty sectors, 0.0 for clean
        """
        density = np.zeros((self.sectors_high, self.sectors_wide), dtype=np.float32)
        
        for sector_row, sector_col in self.dirty_sectors:
            if 0 <= sector_row < self.sectors_high and 0 <= sector_col < self.sectors_wide:
                density[sector_row, sector_col] = 1.0
                
        return density
        
    def get_stats(self) -> Dict[str, Any]:
        """Get sector management statistics.
        
        Returns:
            Dictionary with sector statistics
        """
        dirty_percentage = (len(self.dirty_sectors) / max(1, self.total_sectors)) * 100
        
        return {
            'total_sectors': self.total_sectors,
            'sectors_high': self.sectors_high,
            'sectors_wide': self.sectors_wide,
            'sector_size': self.sector_size,
            'dirty_sectors': len(self.dirty_sectors),
            'dirty_percentage': dirty_percentage,
            'total_dirty_count': self.dirty_count,
            'clean_operations': self.clean_operations,
        }
        
    def reset_stats(self) -> None:
        """Reset sector statistics."""
        self.dirty_count = len(self.dirty_sectors)  # Keep current dirty count
        self.clean_operations = 0
        
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"SectorManager({self.sectors_high}x{self.sectors_wide} sectors, "
                f"size={self.sector_size}, dirty={len(self.dirty_sectors)})")
