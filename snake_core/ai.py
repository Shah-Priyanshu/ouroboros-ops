"""Enhanced AI system for snake survival and pathfinding."""

import random
from typing import List, Tuple, Optional
import numpy as np

from .grid import Grid, DIRECTIONS
from .snake import Snake
from .pathfinding import PathFinder


class SnakeAI:
    """Enhanced AI system that prioritizes survival while seeking food."""
    
    def __init__(self, grid_width: int, grid_height: int):
        """Initialize the AI system.
        
        Args:
            grid_width: Width of the game grid
            grid_height: Height of the game grid
        """
        self.grid_width = grid_width
        self.grid_height = grid_height
        
    def evaluate_move_safety(self, snake: Snake, grid: Grid, direction: int, 
                           look_ahead: int = 3) -> float:
        """Evaluate the safety of a move by looking ahead several steps.
        
        Args:
            snake: The snake to evaluate
            grid: Current game grid
            direction: Direction to evaluate (0=North, 1=East, 2=South, 3=West)
            look_ahead: Number of steps to look ahead
            
        Returns:
            Safety score (higher is safer, 0.0 means certain death)
        """
        if not snake.can_turn(direction):
            return 0.0
            
        # Get the next position
        head_row, head_col = snake.get_head_position()
        dr, dc = DIRECTIONS[direction]
        next_row, next_col = head_row + dr, head_col + dc
        
        # Check bounds
        if (next_row < 0 or next_row >= self.grid_height or 
            next_col < 0 or next_col >= self.grid_width):
            return 0.0
            
        # Check immediate collision with snake body
        if grid.has_snake(next_row, next_col):
            return 0.0
            
        # Start with base safety score
        safety_score = 1.0
        
        # Evaluate space around the next position
        free_spaces = self._count_free_spaces_around(grid, next_row, next_col, look_ahead)
        
        # More free space = safer
        max_possible_spaces = (2 * look_ahead + 1) ** 2
        space_ratio = free_spaces / max_possible_spaces
        safety_score *= space_ratio
        
        # Penalize moves that get too close to walls
        wall_penalty = self._calculate_wall_penalty(next_row, next_col)
        safety_score *= wall_penalty
        
        # Penalize moves that get close to other snakes
        snake_penalty = self._calculate_snake_proximity_penalty(grid, next_row, next_col)
        safety_score *= snake_penalty
        
        # Bonus for moves that keep options open
        escape_routes = self._count_escape_routes(grid, next_row, next_col)
        if escape_routes >= 2:
            safety_score *= 1.2
        elif escape_routes == 1:
            safety_score *= 0.8
        elif escape_routes == 0:
            safety_score *= 0.3
            
        return safety_score
        
    def _count_free_spaces_around(self, grid: Grid, center_row: int, center_col: int, 
                                radius: int) -> int:
        """Count free spaces in a radius around a position."""
        free_count = 0
        for row in range(max(0, center_row - radius), 
                        min(self.grid_height, center_row + radius + 1)):
            for col in range(max(0, center_col - radius), 
                            min(self.grid_width, center_col + radius + 1)):
                if grid.is_walkable(row, col):
                    free_count += 1
        return free_count
        
    def _calculate_wall_penalty(self, row: int, col: int) -> float:
        """Calculate penalty for being close to walls."""
        # Distance from edges
        dist_from_edges = min(row, col, self.grid_height - 1 - row, self.grid_width - 1 - col)
        
        if dist_from_edges <= 1:
            return 0.6  # Strong penalty for being very close to walls
        elif dist_from_edges <= 2:
            return 0.8  # Moderate penalty
        else:
            return 1.0  # No penalty
            
    def _calculate_snake_proximity_penalty(self, grid: Grid, row: int, col: int) -> float:
        """Calculate penalty for being close to other snakes."""
        penalty = 1.0
        
        # Check immediate neighbors
        for dr, dc in DIRECTIONS:
            check_row, check_col = row + dr, col + dc
            if (0 <= check_row < self.grid_height and 
                0 <= check_col < self.grid_width):
                if grid.has_snake(check_row, check_col):
                    penalty *= 0.7
                    
        return penalty
        
    def _count_escape_routes(self, grid: Grid, row: int, col: int) -> int:
        """Count the number of escape routes from a position."""
        escape_count = 0
        
        for dr, dc in DIRECTIONS:
            check_row, check_col = row + dr, col + dc
            if (0 <= check_row < self.grid_height and 
                0 <= check_col < self.grid_width and
                grid.is_walkable(check_row, check_col)):
                escape_count += 1
                
        return escape_count
        
    def detect_potential_trap(self, snake: Snake, grid: Grid, direction: int) -> bool:
        """Detect if a move could lead to a trap (dead end).
        
        Args:
            snake: The snake to check
            grid: Current game grid
            direction: Direction to evaluate
            
        Returns:
            True if this move could lead to a trap
        """
        if not snake.can_turn(direction):
            return True
            
        head_row, head_col = snake.get_head_position()
        dr, dc = DIRECTIONS[direction]
        
        # Check the next position
        next_row, next_col = head_row + dr, head_col + dc
        
        # Check bounds
        if (next_row < 0 or next_row >= self.grid_height or 
            next_col < 0 or next_col >= self.grid_width):
            return True
            
        # Simple trap detection: count available moves from next position
        available_moves = 0
        for check_dr, check_dc in DIRECTIONS:
            check_row = next_row + check_dr
            check_col = next_col + check_dc
            
            if (0 <= check_row < self.grid_height and 
                0 <= check_col < self.grid_width and
                grid.is_walkable(check_row, check_col)):
                available_moves += 1
                
        # If we have less than 2 escape routes, it might be a trap
        return available_moves < 2
        
    def calculate_area_control(self, snake: Snake, grid: Grid, direction: int) -> float:
        """Calculate how much area the snake can control with this move.
        
        Args:
            snake: The snake to evaluate
            grid: Current game grid
            direction: Direction to evaluate
            
        Returns:
            Area control score (higher is better)
        """
        if not snake.can_turn(direction):
            return 0.0
            
        head_row, head_col = snake.get_head_position()
        dr, dc = DIRECTIONS[direction]
        next_row, next_col = head_row + dr, head_col + dc
        
        # Check bounds
        if (next_row < 0 or next_row >= self.grid_height or 
            next_col < 0 or next_col >= self.grid_width):
            return 0.0
            
        # Calculate distance to center of the grid (control center is generally good)
        center_row, center_col = self.grid_height // 2, self.grid_width // 2
        distance_to_center = abs(next_row - center_row) + abs(next_col - center_col)
        max_distance = self.grid_height + self.grid_width
          # Closer to center is better, but not too much weight
        center_score = 1.0 - (distance_to_center / max_distance) * 0.3
        
        return center_score
        
    def find_safest_move(self, snake: Snake, grid: Grid) -> Optional[int]:
        """Find the safest move for a snake, even if it doesn't lead to food.
        
        Args:
            snake: The snake to find a move for
            grid: Current game grid
            
        Returns:
            Best direction to move, or None if no safe moves exist
        """
        # Evaluate all possible directions
        move_scores = []
        
        for direction in range(4):
            if snake.can_turn(direction):
                # Basic safety score
                safety_score = self.evaluate_move_safety(snake, grid, direction)
                
                if safety_score > 0:
                    # Check for potential traps
                    if self.detect_potential_trap(snake, grid, direction):
                        safety_score *= 0.3  # Heavy penalty for trap moves
                      # Check for coiling patterns - this is crucial!
                    if self.detect_coiling_pattern(snake, grid, direction):
                        safety_score *= 0.2  # Very heavy penalty for coiling
                    
                    # Also check for repetitive movement patterns
                    if self.detect_repetitive_movement(snake, direction):
                        safety_score *= 0.4  # Heavy penalty for repetitive movement
                    
                    # Add area control bonus
                    area_control = self.calculate_area_control(snake, grid, direction)
                    safety_score *= area_control
                    
                    # Add expansion potential bonus
                    expansion = self.calculate_expansion_potential(snake, grid, direction)
                    safety_score *= (1.0 + expansion * 0.5)  # Bonus for moves that open up space
                    
                    move_scores.append((direction, safety_score))
                    
        if not move_scores:
            return None
            
        # Sort by safety score (highest first)
        move_scores.sort(key=lambda x: x[1], reverse=True)
        
        # If the best move is significantly better, take it
        # Otherwise, add some randomness among the top moves
        best_score = move_scores[0][1]
        
        # Consider moves within 80% of the best score
        good_moves = [move for move, score in move_scores if score >= best_score * 0.8]
        
        # Return a random choice among good moves
        return random.choice(good_moves)
        
    def find_food_path_with_safety(self, snake: Snake, grid: Grid, pathfinder: PathFinder,
                                  food_positions: List[Tuple[int, int]]) -> Optional[int]:
        """Find a path to food that also considers safety.
        
        Args:
            snake: The snake to find a path for
            grid: Current game grid
            pathfinder: Pathfinding system
            food_positions: List of food positions
            
        Returns:
            Direction to move, or None if no safe path to food exists
        """
        head_row, head_col = snake.get_head_position()
        
        # Try to find a path to food
        path = pathfinder.find_path_to_food(grid, snake.snake_id, head_row, head_col, food_positions)
        
        if path and len(path) > 1:
            # Calculate the direction to the next step in the path
            next_row, next_col = path[1]  # path[0] is current position
            dr, dc = next_row - head_row, next_col - head_col
              # Convert to direction
            for direction, (check_dr, check_dc) in enumerate(DIRECTIONS):
                if dr == check_dr and dc == check_dc:
                    # Check if this move is safe and doesn't cause coiling
                    safety_score = self.evaluate_move_safety(snake, grid, direction)
                    
                    # Also check for coiling when following food paths
                    is_coiling = self.detect_coiling_pattern(snake, grid, direction)
                    
                    if safety_score > 0.3 and not is_coiling:  # Minimum safety threshold + no coiling
                        return direction
                    break
                    
        return None
        
    def decide_move(self, snake: Snake, grid: Grid, pathfinder: PathFinder,
                   food_positions: List[Tuple[int, int]]) -> Optional[int]:
        """Make the best move decision for a snake.
        
        This is the main AI decision function that combines food-seeking with survival.
        
        Args:
            snake: The snake to decide for
            grid: Current game grid
            pathfinder: Pathfinding system
            food_positions: Available food positions
            
        Returns:
            Direction to move, or None if no moves possible
        """
        # First, try to find a safe path to food
        food_direction = self.find_food_path_with_safety(snake, grid, pathfinder, food_positions)
        
        if food_direction is not None:
            return food_direction
            
        # If no safe path to food, prioritize survival
        survival_direction = self.find_safest_move(snake, grid)
        
        return survival_direction

    def detect_coiling_pattern(self, snake: Snake, grid: Grid, direction: int) -> bool:
        """Detect if a move would contribute to a dangerous coiling pattern.
        
        Args:
            snake: The snake to check
            grid: Current game grid
            direction: Direction to evaluate
            
        Returns:
            True if this move would create or continue a coiling pattern
        """
        if not snake.can_turn(direction):
            return True
            
        head_row, head_col = snake.get_head_position()
        dr, dc = DIRECTIONS[direction]
        next_row, next_col = head_row + dr, head_col + dc
        
        # Check bounds
        if (next_row < 0 or next_row >= self.grid_height or 
            next_col < 0 or next_col >= self.grid_width):
            return True
            
        # Get the snake's body positions
        body_positions = set(snake.get_body_positions())
          # Check if we're moving towards our own body (potential coiling)
        danger_radius = 3  # Check within 3 cells
        own_body_nearby = 0
        
        # Get body positions more safely
        try:
            body_positions = set(snake.get_body_positions())
        except:
            # If we can't get body positions, assume it's safe
            return False
        
        for check_row in range(max(0, next_row - danger_radius), 
                              min(self.grid_height, next_row + danger_radius + 1)):
            for check_col in range(max(0, next_col - danger_radius), 
                                  min(self.grid_width, next_col + danger_radius + 1)):
                if (check_row, check_col) in body_positions:
                    distance = abs(check_row - next_row) + abs(check_col - next_col)
                    if distance <= danger_radius:
                        own_body_nearby += 1
        
        # If we're surrounded by too much of our own body, we might be coiling
        body_density_threshold = max(3, len(body_positions) // 4)  # At least 3, or 1/4 of body length
        if own_body_nearby > body_density_threshold:
            return True
            
        # Check for circular movement pattern
        if len(body_positions) >= 4:
            # Get recent positions from the front of the snake
            recent_positions = list(body_positions)[:4]  # First 4 positions (head area)
            
            # Check if we're about to revisit an area we were in recently
            for pos in recent_positions:
                if abs(pos[0] - next_row) <= 1 and abs(pos[1] - next_col) <= 1:
                    return True
                    
        return False
        
    def calculate_expansion_potential(self, snake: Snake, grid: Grid, direction: int) -> float:
        """Calculate how much this move opens up new territory vs closes it off.
        
        Args:
            snake: The snake to evaluate
            grid: Current game grid
            direction: Direction to evaluate
            
        Returns:
            Expansion score (higher means more open territory)
        """
        if not snake.can_turn(direction):
            return 0.0
            
        head_row, head_col = snake.get_head_position()
        dr, dc = DIRECTIONS[direction]
        next_row, next_col = head_row + dr, head_col + dc
        
        # Check bounds
        if (next_row < 0 or next_row >= self.grid_height or 
            next_col < 0 or next_col >= self.grid_width):
            return 0.0
            
        # Count open spaces in the direction we're moving
        expansion_radius = 4
        open_spaces_ahead = 0
        total_spaces_checked = 0
        
        # Look further in the direction we're moving
        for i in range(1, expansion_radius + 1):
            probe_row = next_row + (dr * i)
            probe_col = next_col + (dc * i)
            
            # Also check adjacent cells
            for offset_dr in [-1, 0, 1]:
                for offset_dc in [-1, 0, 1]:
                    check_row = probe_row + offset_dr
                    check_col = probe_col + offset_dc
                    
                    if (0 <= check_row < self.grid_height and 
                        0 <= check_col < self.grid_width):
                        total_spaces_checked += 1
                        if grid.is_walkable(check_row, check_col):
                            open_spaces_ahead += 1
                            
        if total_spaces_checked == 0:
            return 0.0
            
        return open_spaces_ahead / total_spaces_checked
    
    def detect_repetitive_movement(self, snake: Snake, direction: int) -> bool:
        """Detect if the snake is moving in a repetitive pattern that could lead to coiling.
        
        Args:
            snake: The snake to check
            direction: The proposed direction
            
        Returns:
            True if this would create a repetitive movement pattern
        """
        # This would require adding movement history to the snake
        # For now, we'll implement a simpler version that checks if we're 
        # frequently changing direction in a small area
        
        # Check if we're reversing direction too often (sign of coiling)
        current_direction = snake.direction
        
        # If we're turning 180 degrees repeatedly, that's bad
        opposite_direction = (current_direction + 2) % 4
        if direction == opposite_direction:
            return True  # Never allow complete reversal
            
        # If we're turning too sharply too often, that could indicate coiling
        direction_change = abs(direction - current_direction)
        if direction_change == 2:  # 180-degree turn
            return True
        elif direction_change == 3:  # 270-degree turn (equivalent to 90 the other way)
            direction_change = 1
            
        # Frequent 90-degree turns in confined spaces often lead to coiling
        head_row, head_col = snake.get_head_position()
          # Check if we're in a confined area
        open_spaces_nearby = 0
        body_positions = set()
        try:
            body_positions = set(snake.get_body_positions())
        except:
            pass  # If we can't get body positions, continue without this check
            
        for dr in [-2, -1, 0, 1, 2]:
            for dc in [-2, -1, 0, 1, 2]:
                check_row, check_col = head_row + dr, head_col + dc
                if (0 <= check_row < self.grid_height and 
                    0 <= check_col < self.grid_width):
                    # Don't count our own body as "open"
                    if (check_row, check_col) not in body_positions:
                        open_spaces_nearby += 1
                        
        confined_threshold = 15  # Adjust based on testing
        if open_spaces_nearby < confined_threshold and direction_change >= 1:
            return True  # Avoid turning in confined spaces
            
        return False
