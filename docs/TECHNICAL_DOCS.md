# Ouroboros Ops - Technical Documentation

## 📋 Table of Contents
1. [Architecture Overview](#architecture-overview)
2. [Performance Specifications](#performance-specifications)
3. [Core Systems](#core-systems)
4. [API Documentation](#api-documentation)
5. [Configuration Options](#configuration-options)
6. [Troubleshooting](#troubleshooting)

## 🏗️ Architecture Overview

### High-Level Design
Ouroboros Ops uses a modular architecture optimized for high-performance real-time simulation:

```
┌─────────────────┐    ┌─────────────────┐
│   UI Layer      │    │   CLI Tools     │
│  (ui_pygame/)   │    │   (cli/)        │
└─────────┬───────┘    └─────────┬───────┘
          │                      │
          └──────┬───────────────┘
                 │
         ┌───────▼───────┐
         │  Game Engine  │
         │  (engine/)    │
         └───────┬───────┘
                 │
         ┌───────▼───────┐
         │  Snake Core   │
         │ (snake_core/) │
         └───────────────┘
```

### Key Design Principles

1. **Separation of Concerns**
   - `snake_core/`: Pure game logic, no dependencies on graphics or I/O
   - `engine/`: Game loop, event system, performance monitoring
   - `ui_pygame/`: Rendering and input handling
   - `cli/`: Headless simulation and benchmarking tools

2. **Performance-First Architecture**
   - NumPy arrays for bulk operations
   - Numba JIT compilation for hot paths
   - Bit-packed data structures for memory efficiency
   - Sector-based spatial optimization

3. **Event-Driven Updates**
   - Loose coupling between systems
   - Observable state changes
   - Performance profiling integration

## 🚀 Performance Specifications

### Target Metrics
| Metric | Target | Current Status |
|--------|--------|----------------|
| Max Snakes | 5,000+ | ✅ Achieved |
| Frame Rate | 60 FPS | ✅ Stable |
| Grid Size | 256×256 | ✅ Supported |
| Pathfinding Latency | <1ms | ✅ Optimized |
| Memory Usage | <100MB | ✅ Efficient |
| Startup Time | <2s | ✅ Fast |

### Performance Budget (per 16ms frame)
| System | Time Budget | Notes |
|--------|-------------|-------|
| AI Decisions | 6.0ms | Parallelizable |
| Movement/Collision | 1.5ms | Sequential |
| Food Management | 0.2ms | Vectorized |
| Rendering | 4.0ms | GPU-accelerated |
| System Overhead | 4.3ms | Event handling, profiling |

## 🔧 Core Systems

### Grid System (`snake_core/grid.py`)
**Purpose**: High-performance grid state management

**Key Features**:
- Bit-packed uint16 representation
- O(1) collision detection
- SIMD-friendly operations
- Memory-efficient storage

**Cell Encoding**:
```
Bit 0: Food present
Bit 1: Snake body
Bit 2: Snake head
Bits 3-15: Reserved for future use
```

**Usage Example**:
```python
from snake_core.grid import Grid

grid = Grid(256, 256)
grid.place_food(100, 150)
grid.place_snake_head(50, 75)

# Check cell contents
if grid.get_cell(100, 150) & grid.FOOD:
    print("Food found!")
```

### Snake Management (`snake_core/snake.py`)
**Purpose**: Individual snake state and behavior

**State Machine**:
- `ALIVE`: Normal movement and growth
- `DYING`: Collision detected, cleanup in progress
- `DEAD`: Removed from simulation

**Key Methods**:
- `move(direction, grid)`: Execute movement with collision detection
- `grow()`: Increase snake length
- `die(grid)`: Clean removal from grid
- `get_head_position()`: Current head coordinates

### Pathfinding (`snake_core/pathfinding.py`)
**Purpose**: Efficient A* pathfinding with optimizations

**Optimizations**:
- Sector-based caching (16×16 sectors)
- Manhattan distance heuristic
- Early termination for unreachable targets
- Pre-allocated arrays to minimize GC

**Algorithm Flow**:
1. Check sector cache for recent path
2. Run A* with Manhattan heuristic
3. Cache result in sector
4. Return next move direction

### Event System (`engine/event_bus.py`)
**Purpose**: Decoupled inter-system communication

**Event Types**:
- `SNAKE_MOVED`: Snake position changed
- `SNAKE_DIED`: Snake was removed
- `FOOD_EATEN`: Food consumed
- `FOOD_SPAWNED`: New food placed

**Usage**:
```python
from engine.event_bus import event_bus, Event, EventType

# Subscribe to events
def on_snake_death(event):
    print(f"Snake {event.data['snake_id']} died")

event_bus.subscribe(EventType.SNAKE_DIED, on_snake_death)

# Emit events
event_bus.emit(Event(EventType.SNAKE_DIED, {"snake_id": 123}))
```

### Performance Profiler (`engine/profiler.py`)
**Purpose**: Real-time performance monitoring

**Metrics Tracked**:
- Frame time per system
- Memory usage
- GC frequency
- Custom operation timing

**Usage**:
```python
from engine.profiler import profiler

with profiler.profile("pathfinding"):
    # Pathfinding code
    pass

# Export results
profiler.export_csv("performance_log.csv")
```

## 📖 API Documentation

### OuroborosOps Class

```python
class OuroborosOps:
    def __init__(self, 
                 grid_size: int = 256,
                 num_snakes: int = 1000,
                 target_fps: int = 60,
                 window_width: int = 1024,
                 window_height: int = 768,
                 fullscreen: bool = False):
        """Initialize the simulation.
        
        Args:
            grid_size: Grid dimensions (grid_size × grid_size)
            num_snakes: Number of snakes to spawn
            target_fps: Target frame rate
            window_width: Window width in pixels
            window_height: Window height in pixels
            fullscreen: Start in fullscreen mode
        """
```

### GameRenderer Class

```python
class GameRenderer:
    def toggle_fullscreen(self) -> None:
        """Toggle between windowed and fullscreen mode."""
        
    def handle_resize(self, new_width: int, new_height: int) -> None:
        """Handle window resize events."""
        
    def zoom_in(self) -> None:
        """Increase zoom level."""
        
    def zoom_out(self) -> None:
        """Decrease zoom level."""
        
    def reset_view(self) -> None:
        """Reset zoom and pan to defaults."""
```

## ⚙️ Configuration Options

### Command Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--agents` | int | 1000 | Number of snakes |
| `--grid-size` | int | 256 | Grid dimensions |
| `--window-width` | int | 1024 | Window width |
| `--window-height` | int | 768 | Window height |
| `--fullscreen` | flag | False | Start fullscreen |
| `--target-fps` | int | 60 | Target frame rate |

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OUROBOROS_PROFILE` | False | Enable detailed profiling |
| `OUROBOROS_LOG_LEVEL` | INFO | Logging verbosity |
| `OUROBOROS_CACHE_SIZE` | 1024 | Pathfinding cache size |

### Configuration File

Create `config.json` in the project root:

```json
{
    "simulation": {
        "grid_size": 256,
        "num_snakes": 1000,
        "target_fps": 60
    },
    "display": {
        "window_width": 1024,
        "window_height": 768,
        "fullscreen": false,
        "vsync": true
    },
    "performance": {
        "enable_profiling": false,
        "cache_size": 1024,
        "gc_threshold": 1000
    }
}
```

## 🔧 Troubleshooting

### Common Issues

#### Low Frame Rate
**Symptoms**: FPS drops below 60 with many snakes

**Solutions**:
1. Reduce number of snakes (`--agents 500`)
2. Decrease grid size (`--grid-size 128`)
3. Enable profiling to identify bottlenecks
4. Check system resources (CPU, memory)

#### High Memory Usage
**Symptoms**: Memory usage exceeds expected limits

**Solutions**:
1. Reduce pathfinding cache size
2. Force garbage collection more frequently
3. Check for memory leaks in profiler
4. Restart simulation periodically

#### Pathfinding Errors
**Symptoms**: Snakes moving erratically or getting stuck

**Solutions**:
1. Clear pathfinding cache
2. Verify grid state consistency
3. Check for corrupted sectors
4. Restart with fresh grid

#### Display Issues
**Symptoms**: Rendering artifacts or crashes

**Solutions**:
1. Update graphics drivers
2. Try windowed mode instead of fullscreen
3. Adjust window size to match display
4. Check SDL2 compatibility

### Debug Mode

Enable verbose debugging:

```bash
# Set environment variable
set OUROBOROS_LOG_LEVEL=DEBUG

# Run with profiling
python main.py --agents 100 --enable-profiling
```

### Performance Analysis

Generate detailed performance report:

```bash
python -m cli.benchmark --comprehensive --output debug_report.json
```

### Getting Help

1. **Check logs**: Look for error messages in console output
2. **Run diagnostics**: Use built-in benchmark tools
3. **File issues**: Create detailed bug reports on GitHub
4. **Community**: Join discussions for help and tips

## 📊 Monitoring and Metrics

### Real-time Metrics
- Frame rate (FPS)
- Frame time per system
- Memory usage
- Active snake count
- Grid utilization

### Performance Logs
Logs are exported to CSV format with columns:
- Timestamp
- Frame number
- System name
- Execution time (ms)
- Memory usage (MB)

### Benchmarking
Regular benchmarks ensure performance regressions are caught:

```bash
# Quick performance test
python -m cli.benchmark --quick

# Comprehensive scaling test
python -m cli.benchmark --scale --max-snakes 5000

# Regression testing
python -m cli.benchmark --baseline baseline.json
```

---

*This documentation is automatically updated with each release. For the latest version, see the project repository.*
