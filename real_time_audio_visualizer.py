import numpy as np
import sounddevice as sd
from vispy import app, gloo, visuals, scene
import random

# Parameters
samplerate = 44100  # Audio sample rate
duration = 0.1      # Duration per audio block
block_size = int(samplerate * duration)
num_particles = 300  # Number of particles
db_threshold = 50    # Decibel threshold for triggering effects

# Global variable to share audio visualization data
visualization_data = {"amplitude": 0, "fft": [], "frequencies": [], "beat": 0}

# Particle system setup
class ParticleSystem:
    def __init__(self, num_particles):
        self.num_particles = num_particles
        self.positions = np.random.uniform(-1, 1, (num_particles, 3))  # 3D positions
        self.velocities = np.random.uniform(-0.01, 0.01, (num_particles, 3))  # Random 3D velocities
        self.sizes = np.random.uniform(5, 15, num_particles)  # Particle sizes
        self.colors = np.ones((num_particles, 4), dtype=np.float32)  # RGBA colors (white)

    def update(self, amplitude, fft_magnitude):
        """Update particle properties based on audio data."""
        if amplitude > 0:
            # Update positions
            self.positions += self.velocities * (1 + amplitude * 10)

            # Wrap around bounds (-1 to 1 in all directions)
            self.positions = np.where(self.positions > 1, -1, self.positions)
            self.positions = np.where(self.positions < -1, 1, self.positions)

            # Change sizes dynamically
            dominant_size = max(5, min(50, amplitude * 500))
            self.sizes = np.clip(self.sizes + np.random.uniform(-1, 1, self.num_particles), 5, dominant_size)

            # Change colors based on FFT
            if len(fft_magnitude) > 0:
                max_fft_idx = np.argmax(fft_magnitude)
                dominant_color = fft_magnitude[max_fft_idx] / np.max(fft_magnitude)
                self.colors[:, :3] = dominant_color * np.random.uniform(0.5, 1.0, (self.num_particles, 3))

# Audio callback
def audio_callback(indata, frames, time, status):
    """Process audio input and extract visualization data."""
    global visualization_data
    if status:
        print(status)

    audio_block = indata[:, 0]  # Extract single channel
    amplitude = np.abs(audio_block).mean()

    # Compute FFT
    fft = np.fft.fft(audio_block)
    fft_magnitude = np.abs(fft[:len(fft) // 2])
    fft_magnitude_normalized = fft_magnitude / np.max(fft_magnitude) if np.max(fft_magnitude) > 0 else fft_magnitude

    # Beat detection (simplistic: energy in low frequencies)
    beat = np.sum(fft_magnitude[:len(fft_magnitude) // 10])

    # Update visualization data
    visualization_data = {
        "amplitude": amplitude,
        "fft": fft_magnitude_normalized,
        "frequencies": np.fft.fftfreq(len(fft), 1 / samplerate)[:len(fft) // 2],
        "beat": beat
    }

# VisPy Canvas setup
class ParticleCanvas(scene.SceneCanvas):
    def __init__(self):
        scene.SceneCanvas.__init__(self, keys='interactive', size=(800, 600), title="3D Particle Visualization")
        self.unfreeze()

        # Create a viewbox for 3D rendering
        self.view = self.central_widget.add_view()
        self.view.camera = 'arcball'  # Arcball camera for 3D interaction
        self.view.camera.fov = 60  # Field of view

        # Particle system
        self.particle_system = ParticleSystem(num_particles)

        # Create a scatter plot for particles
        self.scatter = scene.visuals.Markers()
        self.view.add(self.scatter)

        self.timer = app.Timer('auto', connect=self.update_particles, start=True)

    def update_particles(self, event):
        """Update particle positions, sizes, and colors."""
        amplitude = visualization_data["amplitude"]
        fft = visualization_data["fft"]

        self.particle_system.update(amplitude, fft)

        # Update scatter plot with new particle data
        self.scatter.set_data(
            pos=self.particle_system.positions,
            size=self.particle_system.sizes,
            face_color=self.particle_system.colors
        )
        self.update()

# Main function
def main():
    global visualization_data

    # Start audio stream
    stream = sd.InputStream(callback=audio_callback, samplerate=samplerate, channels=1, blocksize=block_size)
    stream.start()

    # Create and show the VisPy canvas
    canvas = ParticleCanvas()
    canvas.show()

    # Run the VisPy app
    app.run()

    # Stop audio stream when closing the app
    stream.stop()

if __name__ == "__main__":
    main()
