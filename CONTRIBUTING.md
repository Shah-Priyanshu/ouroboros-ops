# Contributing to Ouroboros Ops

We welcome contributions to Ouroboros Ops! This document provides guidelines for contributing to the project.

## 🚀 Quick Start

1. **Fork** the repository on GitHub
2. **Clone** your fork locally
3. **Set up** the development environment
4. **Create** a feature branch
5. **Make** your changes
6. **Test** thoroughly
7. **Submit** a pull request

## 🔧 Development Setup

### Prerequisites
- Python 3.8+ 
- Git
- Windows/macOS/Linux

### Environment Setup

```bash
# Clone your fork
git clone https://github.com/yourusername/ouroboros-ops.git
cd ouroboros-ops

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate.bat
# Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (if using poetry)
poetry install --with dev

# Run tests to verify setup
python -m pytest tests/ -v
```

## 🧪 Testing Guidelines

### Running Tests

```bash
# Run all tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=snake_core --cov=engine --cov-report=html

# Run specific test categories
python -m pytest tests/test_grid.py -v
python -m pytest tests/test_performance.py -v

# Property-based tests
python -m pytest tests/test_properties.py -v
```

### Test Requirements
- **Unit tests** for all new functions
- **Integration tests** for system interactions
- **Performance tests** for optimization claims
- **Property tests** for algorithm correctness
- Maintain **90%+ coverage**

## 📝 Code Style

### Python Style Guide
- Follow **PEP 8** conventions
- Use **type hints** for all function parameters and returns
- Write **comprehensive docstrings** with performance notes
- Keep lines under **88 characters** (Black formatter)

### Performance Requirements
- All performance-critical code must be **Numba-compatible**
- Use **NumPy arrays** for bulk operations
- Profile changes with the built-in profiler
- Document performance characteristics in docstrings

### Example Code Style

```python
from typing import Tuple
import numpy as np
from numba import njit

@njit(cache=True)
def calculate_distance(point1: Tuple[int, int], point2: Tuple[int, int]) -> float:
    """Calculate Manhattan distance between two points.
    
    Performance: O(1), optimized for Numba JIT compilation.
    
    Args:
        point1: First point coordinates (row, col)
        point2: Second point coordinates (row, col)
        
    Returns:
        Manhattan distance as float
        
    Example:
        >>> calculate_distance((0, 0), (3, 4))
        7.0
    """
    return abs(point1[0] - point2[0]) + abs(point1[1] - point2[1])
```

## 🎯 Performance Standards

### Requirements
- Maintain **60 FPS** with 1000+ snakes
- Pathfinding decisions in **≤1ms**
- Memory usage **<100MB** for max configuration
- Zero performance regression on existing benchmarks

### Profiling
Always profile performance-critical changes:

```python
from engine.profiler import profiler

with profiler.profile("my_optimization"):
    # Your optimized code here
    pass

# Check results
profiler.print_stats()
```

## 🐛 Bug Reports

### Bug Report Template

```markdown
**Bug Description:**
Clear description of the issue

**Steps to Reproduce:**
1. Run command: `python main.py --agents 1000`
2. Wait 30 seconds
3. Press F11 to toggle fullscreen
4. Observe issue

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Environment:**
- OS: Windows 10
- Python: 3.9.7
- Git commit: abc123def

**Performance Impact:**
Does this affect frame rate or memory usage?

**Additional Context:**
Screenshots, logs, profiler output
```

## ✨ Feature Requests

### Feature Request Template

```markdown
**Feature Description:**
Clear description of the proposed feature

**Use Case:**
Why is this feature needed?

**Performance Considerations:**
How might this affect performance?

**Implementation Ideas:**
Any thoughts on implementation approach

**Alternatives:**
Other ways to achieve the same goal
```

## 🔀 Pull Request Process

### Before Submitting
- [ ] Code follows style guidelines
- [ ] All tests pass locally
- [ ] Performance benchmarks show no regression
- [ ] Documentation is updated
- [ ] Commit messages are descriptive

### PR Template

```markdown
**Description:**
Brief description of changes

**Type of Change:**
- [ ] Bug fix
- [ ] New feature
- [ ] Performance optimization
- [ ] Documentation update
- [ ] Refactoring

**Testing:**
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Performance benchmarks run
- [ ] Manual testing completed

**Performance Impact:**
Describe any performance changes (positive or negative)

**Checklist:**
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes (or clearly documented)
```

### Review Process
1. **Automated checks** must pass (tests, linting)
2. **Code review** by maintainer
3. **Performance validation** if applicable
4. **Integration testing** with existing codebase
5. **Merge** when approved

## 🏗️ Architecture Guidelines

### Core Principles
- **Performance First**: Optimize for 5000+ snakes at 60 FPS
- **NumPy + Numba**: Use for all performance-critical paths
- **Bit-packed Data**: Efficient memory usage with uint16 arrays
- **Sector-based**: Spatial partitioning with dirty flags
- **Fixed Timestep**: Maintain 16ms update cycles

### Module Organization

#### snake_core/ (Pure Logic)
- Minimal dependencies (numpy, numba only)
- Numba-compatible functions
- Bit operations for cell state
- Cache-friendly memory patterns

#### engine/ (Systems)
- Fixed-timestep game loop
- Event-driven architecture
- Performance monitoring
- Memory-conscious patterns

#### ui_pygame/ (Rendering)
- SDL2-based graphics
- Fullscreen and windowing support
- Optimized rendering pipeline
- Input handling

### Common Patterns

```python
# Numba-optimized functions
@njit(cache=True)
def optimized_function(grid: np.ndarray) -> np.ndarray:
    """Always include performance notes in docstrings."""
    pass

# Profiling critical sections
with profiler.profile("operation_name"):
    # Critical code here
    pass

# Event-driven updates
event_bus.emit(Event(EventType.SNAKE_MOVED, {"snake_id": snake_id}))

# Bit-flag operations
if grid[row, col] & SNAKE_HEAD:
    # Handle snake head
    pass
```

## 📚 Documentation

### Requirements
- **README.md**: Keep up-to-date with new features
- **Docstrings**: Include performance characteristics
- **Type hints**: All function parameters and returns
- **Comments**: Explain complex algorithms and optimizations

### Documentation Style
- Use **Markdown** for all documentation
- Include **code examples** for new features
- Add **performance notes** for optimizations
- Update **screenshots** when UI changes

## 🙏 Recognition

Contributors will be recognized in:
- **README.md** acknowledgments section
- **CONTRIBUTORS.md** file
- Git commit history
- Release notes for significant contributions

## 📞 Contact

- **Issues**: Use GitHub Issues for bugs and features
- **Discussions**: Use GitHub Discussions for questions
- **Email**: [maintainer@email.com] for security issues

---

Thank you for contributing to Ouroboros Ops! 🐍
