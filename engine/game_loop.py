"""Fixed-timestep game loop with performance monitoring."""

import time
from enum import Enum
from typing import Callable, Optional, List
from dataclasses import dataclass

from .profiler import Profiler
from .event_bus import EventBus, Event, EventType


class GameState(Enum):
    """Game state enumeration."""
    INITIALIZING = "initializing"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"


@dataclass
class FrameStats:
    """Statistics for a single frame."""
    frame_number: int
    total_time: float
    update_time: float
    render_time: float
    fps: float
    snake_count: int
    food_count: int


class GameLoop:
    """High-performance fixed-timestep game loop.
    
    Maintains consistent 60 FPS with separate update and render phases.
    Includes comprehensive performance monitoring and adaptive timing.
    """
    
    def __init__(self, target_fps: int = 60, max_frame_skip: int = 5):
        """Initialize game loop.
        
        Args:
            target_fps: Target frames per second (default 60)
            max_frame_skip: Maximum frames to skip if falling behind
        """
        self.target_fps = target_fps
        self.target_dt = 1.0 / target_fps  # 16.67ms for 60 FPS
        self.max_frame_skip = max_frame_skip
        
        self.state = GameState.INITIALIZING
        self.frame_count = 0
        self.total_time = 0.0
        
        # Timing
        self.last_time = 0.0
        self.accumulator = 0.0
        self.frame_start_time = 0.0
        
        # Performance monitoring
        self.profiler = Profiler()
        self.event_bus = EventBus()
        
        # Frame statistics
        self.frame_stats: List[FrameStats] = []
        self.max_stats_history = 1000
        
        # Callbacks
        self.update_callback: Optional[Callable[[float], None]] = None
        self.render_callback: Optional[Callable[[float], None]] = None
        self.stats_callback: Optional[Callable[[FrameStats], None]] = None
        
        # Performance tracking
        self.fps_samples: List[float] = []
        self.max_fps_samples = 60
        self.current_fps = 0.0
        
    def set_update_callback(self, callback: Callable[[float], None]) -> None:
        """Set callback for update phase.
        
        Args:
            callback: Function called with delta time for each update
        """
        self.update_callback = callback
        
    def set_render_callback(self, callback: Callable[[float], None]) -> None:
        """Set callback for render phase.
        
        Args:
            callback: Function called with interpolation factor for rendering
        """
        self.render_callback = callback
        
    def set_stats_callback(self, callback: Callable[[FrameStats], None]) -> None:
        """Set callback for frame statistics.
        
        Args:
            callback: Function called with frame stats after each frame
        """
        self.stats_callback = callback
        
    def start(self) -> None:
        """Start the game loop."""
        if self.state != GameState.INITIALIZING:
            return
            
        self.state = GameState.RUNNING
        self.last_time = time.perf_counter()
        self.frame_start_time = self.last_time
        
        # Emit start event
        self.event_bus.emit(Event(EventType.GAME_STARTED, {"timestamp": self.last_time}))
        
    def pause(self) -> None:
        """Pause the game loop."""
        if self.state == GameState.RUNNING:
            self.state = GameState.PAUSED
            self.event_bus.emit(Event(EventType.GAME_PAUSED, {"frame": self.frame_count}))
            
    def resume(self) -> None:
        """Resume the game loop from pause."""
        if self.state == GameState.PAUSED:
            self.state = GameState.RUNNING
            self.last_time = time.perf_counter()  # Reset timing
            self.event_bus.emit(Event(EventType.GAME_RESUMED, {"frame": self.frame_count}))
            
    def stop(self) -> None:
        """Stop the game loop."""
        self.state = GameState.STOPPED
        self.event_bus.emit(Event(EventType.GAME_STOPPED, {
            "frame": self.frame_count,
            "total_time": self.total_time
        }))
        
    def tick(self) -> bool:
        """Execute one iteration of the game loop.
        
        Returns:
            True if loop should continue, False if stopped
        """
        if self.state != GameState.RUNNING:
            return self.state != GameState.STOPPED
            
        self.frame_start_time = time.perf_counter()
        current_time = self.frame_start_time
        frame_time = current_time - self.last_time
        self.last_time = current_time
        
        # Prevent spiral of death with large frame times
        frame_time = min(frame_time, self.target_dt * self.max_frame_skip)
        self.accumulator += frame_time
        
        update_time = 0.0
        updates_performed = 0
        
        # Fixed timestep updates
        while self.accumulator >= self.target_dt and updates_performed < self.max_frame_skip:
            with self.profiler.profile("update") as update_timer:
                if self.update_callback:
                    self.update_callback(self.target_dt)
                    
            update_time += update_timer.elapsed_time
            self.accumulator -= self.target_dt
            updates_performed += 1
            
        # Interpolation factor for smooth rendering
        interpolation = self.accumulator / self.target_dt
        
        # Render phase
        render_time = 0.0
        with self.profiler.profile("render") as render_timer:
            if self.render_callback:
                self.render_callback(interpolation)
        render_time = render_timer.elapsed_time
        
        # Update frame statistics
        total_frame_time = time.perf_counter() - self.frame_start_time
        self.total_time += total_frame_time
        self.frame_count += 1
        
        # Calculate FPS
        if frame_time > 0:
            current_fps = 1.0 / frame_time
            self.fps_samples.append(current_fps)
            if len(self.fps_samples) > self.max_fps_samples:
                self.fps_samples.pop(0)
            self.current_fps = sum(self.fps_samples) / len(self.fps_samples)
            
        # Create frame stats
        frame_stats = FrameStats(
            frame_number=self.frame_count,
            total_time=total_frame_time,
            update_time=update_time,
            render_time=render_time,
            fps=self.current_fps,
            snake_count=0,  # To be filled by callback
            food_count=0   # To be filled by callback
        )
        
        # Store frame stats
        self.frame_stats.append(frame_stats)
        if len(self.frame_stats) > self.max_stats_history:
            self.frame_stats.pop(0)
            
        # Call stats callback
        if self.stats_callback:
            self.stats_callback(frame_stats)
            
        return True
        
    def run(self) -> None:
        """Run the game loop until stopped."""
        self.start()
        
        try:
            while self.tick():
                # Optional yield for cooperative multitasking
                if self.frame_count % 60 == 0:  # Every second
                    time.sleep(0.001)  # 1ms yield
        except KeyboardInterrupt:
            print("\\nGame loop interrupted by user")
        finally:
            self.stop()
            
    def get_average_fps(self, frames: int = 60) -> float:
        """Get average FPS over last N frames.
        
        Args:
            frames: Number of recent frames to average
            
        Returns:
            Average FPS
        """
        if not self.frame_stats:
            return 0.0
            
        recent_stats = self.frame_stats[-frames:]
        if not recent_stats:
            return 0.0
            
        return sum(stat.fps for stat in recent_stats) / len(recent_stats)
        
    def get_performance_summary(self) -> dict:
        """Get comprehensive performance summary.
        
        Returns:
            Dictionary with performance metrics
        """
        if not self.frame_stats:
            return {}
            
        recent_stats = self.frame_stats[-60:]  # Last second
        
        return {
            'frame_count': self.frame_count,
            'total_time': self.total_time,
            'average_fps': self.get_average_fps(),
            'current_fps': self.current_fps,
            'target_fps': self.target_fps,
            'avg_frame_time': sum(s.total_time for s in recent_stats) / len(recent_stats) if recent_stats else 0,
            'avg_update_time': sum(s.update_time for s in recent_stats) / len(recent_stats) if recent_stats else 0,
            'avg_render_time': sum(s.render_time for s in recent_stats) / len(recent_stats) if recent_stats else 0,
            'profiler_stats': self.profiler.get_summary(),
        }
        
    def reset_stats(self) -> None:
        """Reset all performance statistics."""
        self.frame_stats.clear()
        self.fps_samples.clear()
        self.profiler.reset()
        self.frame_count = 0
        self.total_time = 0.0
        
    def is_running(self) -> bool:
        """Check if game loop is currently running."""
        return self.state == GameState.RUNNING
        
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"GameLoop(fps={self.current_fps:.1f}/{self.target_fps}, "
                f"frame={self.frame_count}, state={self.state.value})")
