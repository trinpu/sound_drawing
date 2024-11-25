# Drawing with Sound

Drawing images from real-time sound recordings.

## High-Level Overview

* Input: Real-time audio capture using a microphone or streaming source.
* Processing: Real-time extraction of audio features (amplitude, frequency spectrum, etc.).
* Visualization: Generating and rendering images dynamically based on extracted features.
* Output: Continuous visual display synced with the real-time audio.

## Architecture
The project has three primary layers:

1. Real-time audio capture (Input layer)
2. Audio analysis and feature extraction (Processing layer)
3. Dynamic image generation and rendering (Output layer)

## Optional Enhancements
Add Interactivity: Use keyboard or mouse inputs to manipulate visuals.
Advanced Visuals: Integrate shaders using moderngl for GPU-accelerated graphics.
3D Visualizations: Use Python libraries like vispy or pythreejs.

