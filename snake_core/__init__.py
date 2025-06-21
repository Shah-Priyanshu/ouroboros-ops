"""Snake Core - High-performance pure-logic package for Ouroboros Ops.

This package contains all performance-critical components with minimal dependencies.
Only numpy is required for SIMD-friendly operations.
"""

__version__ = "0.1.0"

from .grid import Grid, EMPTY, FOOD, SNAKE_BODY, SNAKE_HEAD
from .snake import Snake, SnakeState
from .food import FoodManager
from .pathfinding import PathFinder
from .spatial import SectorManager
from .ai import SnakeAI

__all__ = [
    "Grid",
    "EMPTY",
    "FOOD", 
    "SNAKE_BODY",
    "SNAKE_HEAD",
    "Snake", 
    "SnakeState",
    "FoodManager",
    "PathFinder", 
    "SectorManager",
    "SnakeAI",
]
