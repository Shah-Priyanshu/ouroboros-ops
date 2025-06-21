"""Event system for decoupled communication between game components."""

from enum import Enum
from typing import Any, Dict, List, Callable, Optional
from dataclasses import dataclass
import weakref


class EventType(Enum):
    """Event type enumeration."""
    # Game lifecycle
    GAME_STARTED = "game_started"
    GAME_PAUSED = "game_paused"
    GAME_RESUMED = "game_resumed"
    GAME_STOPPED = "game_stopped"
    
    # Snake events
    SNAKE_SPAWNED = "snake_spawned"
    SNAKE_DIED = "snake_died"
    SNAKE_MOVED = "snake_moved"
    SNAKE_ATE_FOOD = "snake_ate_food"
    SNAKE_GREW = "snake_grew"
    
    # Food events
    FOOD_SPAWNED = "food_spawned"
    FOOD_CONSUMED = "food_consumed"
    
    # Pathfinding events
    PATH_COMPUTED = "path_computed"
    PATH_BLOCKED = "path_blocked"
    SECTOR_DIRTY = "sector_dirty"
    
    # Performance events
    FRAME_COMPLETED = "frame_completed"
    PERFORMANCE_WARNING = "performance_warning"
    
    # Custom events
    CUSTOM = "custom"


@dataclass
class Event:
    """Event data structure."""
    event_type: EventType
    data: Dict[str, Any]
    timestamp: Optional[float] = None
    source: Optional[str] = None
    
    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            import time
            self.timestamp = time.perf_counter()


class EventBus:
    """High-performance event bus with weak references to prevent memory leaks.
    
    Provides pub/sub pattern for decoupled communication between game components.
    Uses weak references for automatic cleanup of dead listeners.
    """
    
    def __init__(self):
        """Initialize event bus."""
        # Weak references to prevent memory leaks
        self._listeners: Dict[EventType, List[weakref.ReferenceType]] = {}
        self._one_time_listeners: Dict[EventType, List[weakref.ReferenceType]] = {}
        
        # Statistics
        self.events_emitted = 0
        self.events_processed = 0
        self.listener_count = 0
        
    def subscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """Subscribe to an event type.
        
        Args:
            event_type: Type of event to listen for
            callback: Function to call when event is emitted
        """
        if event_type not in self._listeners:
            self._listeners[event_type] = []
            
        # Use weak reference to allow garbage collection
        weak_callback = weakref.ref(callback)
        self._listeners[event_type].append(weak_callback)
        self.listener_count += 1
        
    def subscribe_once(self, event_type: EventType, callback: Callable[[Event], None]) -> None:
        """Subscribe to an event type for one-time notification.
        
        Args:
            event_type: Type of event to listen for
            callback: Function to call when event is emitted (once only)
        """
        if event_type not in self._one_time_listeners:
            self._one_time_listeners[event_type] = []
            
        weak_callback = weakref.ref(callback)
        self._one_time_listeners[event_type].append(weak_callback)
        
    def unsubscribe(self, event_type: EventType, callback: Callable[[Event], None]) -> bool:
        """Unsubscribe from an event type.
        
        Args:
            event_type: Type of event to stop listening for
            callback: Callback function to remove
            
        Returns:
            True if callback was found and removed
        """
        if event_type not in self._listeners:
            return False
            
        # Find and remove callback
        listeners = self._listeners[event_type]
        for i, weak_callback in enumerate(listeners):
            if weak_callback() is callback:
                listeners.pop(i)
                self.listener_count -= 1
                return True
                
        return False
        
    def emit(self, event: Event) -> int:
        """Emit an event to all subscribers.
        
        Args:
            event: Event to emit
            
        Returns:
            Number of listeners that processed the event
        """
        self.events_emitted += 1
        processed_count = 0
        
        # Process regular listeners
        if event.event_type in self._listeners:
            listeners = self._listeners[event.event_type]
            
            # Clean up dead weak references and call live ones
            live_listeners = []
            for weak_callback in listeners:
                callback = weak_callback()
                if callback is not None:
                    live_listeners.append(weak_callback)
                    try:
                        callback(event)
                        processed_count += 1
                    except Exception as e:
                        print(f"Error in event listener: {e}")
                        
            # Update listener list with only live references
            self._listeners[event.event_type] = live_listeners
            
        # Process one-time listeners
        if event.event_type in self._one_time_listeners:
            listeners = self._one_time_listeners[event.event_type]
            
            for weak_callback in listeners:
                callback = weak_callback()
                if callback is not None:
                    try:
                        callback(event)
                        processed_count += 1
                    except Exception as e:
                        print(f"Error in one-time event listener: {e}")
                        
            # Clear one-time listeners after processing
            self._one_time_listeners[event.event_type] = []
            
        self.events_processed += processed_count
        return processed_count
        
    def emit_simple(self, event_type: EventType, data: Dict[str, Any] = None, 
                    source: str = None) -> int:
        """Emit a simple event without creating Event object explicitly.
        
        Args:
            event_type: Type of event
            data: Event data dictionary
            source: Source identifier
            
        Returns:
            Number of listeners that processed the event
        """
        event = Event(event_type, data or {}, source=source)
        return self.emit(event)
        
    def clear_listeners(self, event_type: Optional[EventType] = None) -> None:
        """Clear event listeners.
        
        Args:
            event_type: Specific event type to clear, or None for all
        """
        if event_type is None:
            self._listeners.clear()
            self._one_time_listeners.clear()
            self.listener_count = 0
        else:
            if event_type in self._listeners:
                self.listener_count -= len(self._listeners[event_type])
                del self._listeners[event_type]
            if event_type in self._one_time_listeners:
                del self._one_time_listeners[event_type]
                
    def cleanup_dead_references(self) -> int:
        """Clean up dead weak references.
        
        Returns:
            Number of dead references removed
        """
        removed = 0
        
        # Clean regular listeners
        for event_type, listeners in self._listeners.items():
            live_listeners = []
            for weak_callback in listeners:
                if weak_callback() is not None:
                    live_listeners.append(weak_callback)
                else:
                    removed += 1
                    self.listener_count -= 1
            self._listeners[event_type] = live_listeners
            
        # Clean one-time listeners
        for event_type, listeners in self._one_time_listeners.items():
            live_listeners = []
            for weak_callback in listeners:
                if weak_callback() is not None:
                    live_listeners.append(weak_callback)
                else:
                    removed += 1
            self._one_time_listeners[event_type] = live_listeners
            
        return removed
        
    def get_listener_count(self, event_type: Optional[EventType] = None) -> int:
        """Get number of listeners for event type.
        
        Args:
            event_type: Specific event type, or None for total count
            
        Returns:
            Number of listeners
        """
        if event_type is None:
            return self.listener_count
            
        count = 0
        if event_type in self._listeners:
            count += len(self._listeners[event_type])
        if event_type in self._one_time_listeners:
            count += len(self._one_time_listeners[event_type])
            
        return count
        
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics.
        
        Returns:
            Dictionary with statistics
        """
        return {
            'events_emitted': self.events_emitted,
            'events_processed': self.events_processed,
            'listener_count': self.listener_count,
            'event_types_with_listeners': len(self._listeners),
            'one_time_listeners': sum(len(listeners) for listeners in self._one_time_listeners.values()),
        }
        
    def reset_stats(self) -> None:
        """Reset event statistics."""
        self.events_emitted = 0
        self.events_processed = 0
        
    def __repr__(self) -> str:
        """String representation for debugging."""
        return (f"EventBus(listeners={self.listener_count}, "
                f"emitted={self.events_emitted}, processed={self.events_processed})")
