"""Pygame-based renderer for high-performance visualization."""

import pygame
import numpy as np
from typing import Optional, Tuple

from snake_core import Grid


class GameRenderer:
    """High-performance pygame renderer with zoom and pan support.
    
    Optimized for rendering large grids with thousands of entities at 60 FPS.
    Uses pygame surfaces and optimized blitting for maximum performance.    """
    
    def __init__(self, grid_width: int, grid_height: int, 
                 window_width: int = 1024, window_height: int = 768,
                 fullscreen: bool = False):
        """Initialize renderer.
        
        Args:
            grid_width: Grid width in cells
            grid_height: Grid height in cells  
            window_width: Window width in pixels
            window_height: Window height in pixels
            fullscreen: Start in fullscreen mode
        """
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.window_width = window_width
        self.window_height = window_height
        self.fullscreen = fullscreen
        
        # Pygame components
        self.screen: Optional[pygame.Surface] = None
        self.grid_surface: Optional[pygame.Surface] = None
        self.clock = pygame.time.Clock()
        
        # Rendering parameters
        self.cell_size = min(window_width // grid_width, window_height // grid_height)
        self.cell_size = max(self.cell_size, 2)  # Minimum 2 pixels per cell
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        
        # State
        self.should_quit = False
        
        # Colors
        self.colors = {
            'empty': (20, 20, 30),      # Dark blue-gray
            'food': (255, 100, 100),     # Red
            'snake_head': (100, 255, 100), # Green
            'snake_body': (50, 150, 50),   # Dark green
            'snake_dying': (100, 100, 255), # Blue for dying snakes
            'background': (10, 10, 15),    # Very dark
        }
        
        # Performance tracking
        self.frames_rendered = 0
        self.last_render_time = 0.0        
        # Grid cache for optimization        self.last_grid_state = None
        self.grid_dirty = True
        
    def initialize(self) -> None:
        """Initialize pygame and create surfaces."""
        print("Initializing pygame...")
        pygame.init()
        print("Pygame initialized successfully")
        
        pygame.display.set_caption("Ouroboros Ops - Snake Battleground")
        print("Window caption set")
        
        # Create display with fullscreen support
        if self.fullscreen:
            print("Creating fullscreen display mode")
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
            # Update window dimensions to actual screen size
            self.window_width = self.screen.get_width()
            self.window_height = self.screen.get_height()
            print(f"Fullscreen mode: {self.window_width}x{self.window_height}")
        else:
            print(f"Creating windowed display mode: {self.window_width}x{self.window_height}")
            self.screen = pygame.display.set_mode((self.window_width, self.window_height), pygame.RESIZABLE)
            print("Windowed mode created successfully")
        
        # Recalculate cell size based on actual window dimensions
        self.cell_size = min(self.window_width // self.grid_width, self.window_height // self.grid_height)
        self.cell_size = max(self.cell_size, 1)  # Minimum 1 pixel per cell
          # Create grid surface for efficient rendering
        grid_pixel_width = self.grid_width * self.cell_size
        grid_pixel_height = self.grid_height * self.cell_size
        print(f"Creating grid surface: {grid_pixel_width}x{grid_pixel_height} (cell size: {self.cell_size}px)")
        self.grid_surface = pygame.Surface((grid_pixel_width, grid_pixel_height))
        print("Grid surface created successfully")
        print("Renderer initialization complete")
        
    def render(self, grid: Grid, snakes, interpolation: float = 0.0) -> None:
        """Render the current game state.
        
        Args:
            grid: Game grid to render
            snakes: List of snake objects
            interpolation: Interpolation factor for smooth animation (0.0 to 1.0)
        """
        if not self.screen:
            return
            
        # Handle pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:                self.should_quit = True
                # Don't return here - continue with rendering
            elif event.type == pygame.KEYDOWN:
                self.handle_keydown(event)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mouse_click(event)
            elif event.type == pygame.VIDEORESIZE:
                self.handle_window_resize(event.w, event.h)
                
        # Always update grid surface (remove optimization for now)
        self.render_grid_to_surface(grid, snakes)
        self.grid_dirty = False
            
        # Clear screen
        self.screen.fill(self.colors['background'])
          # Simple direct blit without complex viewport logic
        if self.grid_surface:
            # Calculate centering offset
            grid_pixel_width = self.grid_width * self.cell_size
            grid_pixel_height = self.grid_height * self.cell_size
            
            offset_x = (self.window_width - grid_pixel_width) // 2
            offset_y = (self.window_height - grid_pixel_height) // 2
            
            self.screen.blit(self.grid_surface, (offset_x, offset_y))
        
        # Render UI overlay
        self.render_ui_overlay(grid)
          # Update display
        pygame.display.flip()
        self.clock.tick()  # Update clock for FPS calculation
        self.frames_rendered += 1
        
    def render_grid_to_surface(self, grid: Grid, snakes) -> None:
        """Render grid state to the grid surface.
        
        Args:
            grid: Game grid to render
            snakes: List of snake objects (dying snakes will not be rendered)
        """
        if not self.grid_surface:
            return
            
        # Fill background
        self.grid_surface.fill(self.colors['empty'])
        
        # Render cells efficiently
        grid_array = grid.grid
        
        for row in range(self.grid_height):
            for col in range(self.grid_width):
                cell_value = grid_array[row, col]
                
                if cell_value == 0:  # Empty
                    continue  # Already filled with background
                    
                # Calculate pixel position
                x = col * self.cell_size
                y = row * self.cell_size
                rect = pygame.Rect(x, y, self.cell_size, self.cell_size)
                
                # Choose color based on cell contents
                if cell_value & 4:  # Snake head
                    color = self.colors['snake_head']
                elif cell_value & 2:  # Snake body
                    color = self.colors['snake_body']
                elif cell_value & 1:  # Food
                    color = self.colors['food']
                else:
                    continue
                    
                pygame.draw.rect(self.grid_surface, color, rect)
    def render_ui_overlay(self, grid: Grid) -> None:
        """Render UI overlay with statistics."""
        if not pygame.font.get_init():
            pygame.font.init()
            
        font = pygame.font.Font(None, 24)
        
        # Get grid statistics
        empty, food, body, head = grid.count_cell_types()
        
        # Create text surfaces
        stats_text = [
            f"Snakes: {head}",
            f"Food: {food}",
            f"FPS: {self.clock.get_fps():.1f}",
            f"Frames: {self.frames_rendered}",        ]
        
        # Render text
        y_offset = 10
        for text in stats_text:
            text_surface = font.render(text, True, (255, 255, 255))
            self.screen.blit(text_surface, (10, y_offset))
            y_offset += 25
            
    def handle_keydown(self, event) -> None:
        """Handle keyboard input."""
        if event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
            self.zoom_in()
        elif event.key == pygame.K_MINUS:
            self.zoom_out()
        elif event.key == pygame.K_r:
            self.reset_view()
        elif event.key == pygame.K_SPACE:
            self.grid_dirty = True  # Force refresh
        elif event.key == pygame.K_F11:
            self.toggle_fullscreen()
        elif event.key == pygame.K_ESCAPE and self.fullscreen:
            self.toggle_fullscreen()  # Exit fullscreen with ESC
            
        # Pan controls
        pan_speed = 20
        if event.key == pygame.K_LEFT:
            self.pan_x += pan_speed
        elif event.key == pygame.K_RIGHT:
            self.pan_x -= pan_speed
        elif event.key == pygame.K_UP:
            self.pan_y += pan_speed
        elif event.key == pygame.K_DOWN:
            self.pan_y -= pan_speed
            
    def handle_mouse_click(self, event) -> None:
        """Handle mouse clicks."""
        if event.button == 4:  # Mouse wheel up
            self.zoom_in()
        elif event.button == 5:  # Mouse wheel down
            self.zoom_out()
            
    def zoom_in(self) -> None:
        """Zoom in on the grid."""
        self.zoom = min(self.zoom * 1.2, 10.0)
        
    def zoom_out(self) -> None:
        """Zoom out from the grid."""
        self.zoom = max(self.zoom / 1.2, 0.1)
        
    def reset_view(self) -> None:
        """Reset zoom and pan to default."""
        self.zoom = 1.0
        self.pan_x = 0
        self.pan_y = 0
        
    def cleanup(self) -> None:
        """Clean up pygame resources."""
        pygame.quit()
        
    def get_stats(self) -> dict:
        """Get renderer statistics."""
        return {
            'frames_rendered': self.frames_rendered,
            'current_fps': self.clock.get_fps(),
            'zoom': self.zoom,
            'pan': (self.pan_x, self.pan_y),
            'cell_size': self.cell_size,
            'grid_dirty': self.grid_dirty,
        }
        
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"GameRenderer({self.grid_width}x{self.grid_height}, "
                f"zoom={self.zoom:.1f}, frames={self.frames_rendered})")
