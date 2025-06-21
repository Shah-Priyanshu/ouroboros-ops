# Demo Video

Ouroboros Ops demo video showcasing the high-performance snake simulation in action.

## Video Details

- **File**: `docs/demo_video.mp4`
- **Duration**: 18.8 seconds
- **Resolution**: 1280x720 (720p HD)
- **Frame Rate**: 30 FPS
- **Format**: MP4 (H.264)
- **File Size**: 7.8 MB

## Video Content

The demo video shows:
- 80 snakes spawning with optimized spacing for better survival
- Extended real-time simulation lasting 55+ seconds (captured at 30 FPS)
- Advanced pathfinding and movement behavior over time
- Snake-to-snake interactions, collisions, and death mechanics
- Gradual population decline from 80 → 43 → 29 → 18 → 13 → 9 → 4 → 3 snakes
- Performance metrics overlay showing elapsed time and live snake count
- Stable frame rate throughout the entire simulation

## Video Creation Process

The video was created using automated frame capture with intelligent stopping:

1. **Improved Frame Capture**: Used `capture_demo_improved.py` with smart stopping conditions
2. **Extended Runtime**: Captured 563 frames over 55.3 seconds of simulation
3. **Better Survival**: Reduced snake count (80 vs 200) for less crowding and longer gameplay
4. **Smart Stopping**: Automatically stopped when ≤3 snakes remained after 20s minimum
5. **Video Assembly**: Used `create_video_from_frames.py` with OpenCV to create MP4

### Technical Details

```bash
# Capture improved frames with smart stopping
python capture_demo_improved.py

# Create video from frames  
python create_video_from_frames.py
```

Enhanced capture settings:
- **Grid Size**: 128x128 cells
- **Snake Count**: 80 initial agents (reduced for better survival)
- **Duration Range**: 20-60 seconds with intelligent stopping
- **Stopping Condition**: ≤3 snakes remaining after 20s minimum
- **Cell Size**: 5 pixels per cell
- **Update Rate**: 60 FPS simulation, 30 FPS capture
- **Frame Count**: 563 frames captured

## Video Improvements

This improved version addresses the original issues:

### ✅ **Fixed: Continues after all snakes die**
- **Smart stopping conditions**: Stops when ≤3 snakes remain after minimum duration
- **No empty footage**: Video ends when meaningful action stops

### ✅ **Fixed: Snakes die too quickly**  
- **Reduced crowding**: 80 snakes instead of 200 for less competition
- **Better spacing**: Improved initial spawn locations to avoid immediate collisions
- **Extended gameplay**: 18.8 seconds of engaging content vs 6.5 seconds

### ✅ **Enhanced: Better demonstration value**
- **Population tracking**: Shows natural decline over time
- **Performance overlay**: Real-time statistics and frame counter
- **Smooth progression**: Gradual reduction from 80 to 3 snakes
- **Professional quality**: 1280x720 HD at stable 30 FPS

## Video Hosting

For embedding in documentation and sharing:

### Upload Options
- **YouTube**: For public sharing and embedding
- **GitHub Releases**: Direct download for users
- **Repository**: Local reference in docs/

### Embedding Code
```html
<!-- For GitHub README -->
<video width="640" height="360" controls>
  <source src="docs/demo_video.mp4" type="video/mp4">
  Your browser does not support the video tag.
</video>
```

```markdown
<!-- For Markdown documents -->
![Demo Video](docs/demo_video.mp4)
```

## Usage in Documentation

The video demonstrates key features mentioned in:
- **README.md**: Main project overview and features
- **TECHNICAL_DOCS.md**: Performance capabilities and scalability
- **CONTRIBUTING.md**: Expected system behavior for development

## Future Improvements

For extended demo videos:
- **Higher Agent Count**: Demonstrate 1000+ snakes for performance showcase
- **Feature Showcase**: Fullscreen mode, CLI tools, benchmarking interface
- **Performance Graphs**: Real-time FPS and memory usage visualization
- **Multiple Scenarios**: Different grid sizes and agent configurations
- **Narration**: Voice-over explaining key features and performance metrics
