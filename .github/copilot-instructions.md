<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

# Ouroboros Ops - Copilot Instructions

This is a high-performance Python project for a massively-autonomous Snake battleground simulation. The project emphasizes performance optimization, real-time processing, and scalable architecture.

## Key Principles

- **Performance First**: All code should be optimized for handling 5,000+ concurrent snakes at 60 FPS
- **NumPy + Numba**: Use NumPy arrays and Numba JIT compilation for performance-critical paths
- **Bit-packed Data**: Use bit flags in uint16 arrays for efficient memory usage
- **Sector-based Optimization**: Spatial partitioning with dirty flags to minimize computations
- **Fixed Timestep**: Maintain consistent 16ms update cycles regardless of frame rate

## Architecture Guidelines

### snake_core/ (Pure Logic)
- Contains all game logic with minimal dependencies (numpy, numba only)
- Functions should be Numba-compatible where possible
- Use bit operations for cell state management
- Optimize for cache-friendly memory access patterns

### engine/ (Systems)
- Fixed-timestep game loop with performance profiling
- Event-driven architecture with weak references
- Comprehensive performance monitoring and CSV export
- Memory-conscious design patterns

### Pathfinding Optimization
- A* algorithm with Manhattan distance heuristic
- Sector-based caching to avoid redundant computations
- Pre-allocated arrays to minimize garbage collection
- Early termination and path validation

## Performance Targets

- **Scale**: ≥5,000 snakes on 256×256 grid
- **Framerate**: Consistent 60 FPS
- **Response Time**: Pathfinding decisions in ≤1ms
- **Memory**: <100MB total for maximum configuration

## Code Style

- Type hints for all function parameters and returns
- Comprehensive docstrings with performance notes
- Profile-guided optimization using the built-in profiler
- Property-based testing for algorithm correctness
- Benchmark-driven development

## Common Patterns

```python
# Numba-optimized functions
@njit(cache=True)
def fast_function(grid: np.ndarray, ...) -> ...:
    # Implementation
    
# Profiling critical sections
with profiler.profile("operation_name"):
    # Critical code
    
# Event-driven state changes
event_bus.emit(Event(EventType.SNAKE_MOVED, {"snake_id": id}))

# Bit-flag operations
if grid[row, col] & SNAKE_HEAD:
    # Handle snake head
```

## Testing Strategy

- Unit tests for all core algorithms
- Property-based testing with Hypothesis
- Performance regression tests
- Integration tests for end-to-end scenarios
- Benchmark suites for optimization validation

When suggesting code improvements, prioritize:
1. Performance impact (frame time reduction)
2. Memory efficiency (reduced allocations)
3. Algorithmic complexity improvements
4. Cache-friendly data access patterns
5. Numba JIT compatibility
