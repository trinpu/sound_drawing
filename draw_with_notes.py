import numpy as np
import sounddevice as sd
from vispy import app, visuals, scene
import random

# Parameters
samplerate = 22050  # Reduced sampling rate for Raspberry Pi
duration = 0.2      # Increased duration per audio block
block_size = int(samplerate * duration)
db_threshold = 50    # Decibel threshold for triggering effects
visualization_data = {"amplitude": 0, "fft": [], "frequencies": [], "dominant_note": "N/A"}

# Galaxy-inspired color palette
galaxy_colors = [
    (0.5, 0.5, 1.0, 1.0),  # Blue-white
    (1.0, 1.0, 0.8, 1.0),  # Warm white
    (0.8, 0.6, 1.0, 1.0),  # Lavender
    (0.6, 0.6, 0.9, 1.0),  # Soft blue
    (0.8, 0.8, 1.0, 1.0)   # Pale violet
]

def audio_callback(indata, frames, time, status):
    if status:
        print(status)
    audio_block = indata[:, 0]
    process_audio(audio_block)

def frequency_to_note(frequency):
    if frequency <= 0:
        return "N/A"
    midi_note = 69 + 12 * np.log2(frequency / 440.0)
    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    note_index = int(round(midi_note)) % 12
    return note_names[note_index]

def process_audio(audio_block):
    global visualization_data
    amplitude = np.abs(audio_block).mean()
    if amplitude > 0:
        decibels = 20 * np.log10(amplitude) + 100
    else:
        decibels = 0

    fft = np.fft.fft(audio_block)
    frequencies = np.fft.fftfreq(len(fft), 1 / samplerate)
    fft_magnitude = np.abs(fft[:len(fft) // 2])
    max_index = np.argmax(fft_magnitude)
    dominant_frequency = frequencies[max_index]
    dominant_note = frequency_to_note(dominant_frequency)

    visualization_data = {
        "amplitude": amplitude,
        "decibels": decibels,
        "dominant_note": dominant_note
    }

class ParticleSystem:
    def __init__(self):
        self.particles = []

    def create_particles(self, amplitude, dominant_note):
        if len(self.particles) >= 100:  # Limit total particles
            return

        for _ in range(5):  # Create up to 5 particles per note
            position = np.random.uniform(-1, 1, 3)
            size = max(5, amplitude * 50)
            color = np.clip(np.array(random.choice(galaxy_colors), dtype=np.float32), 0.0, 1.0)  # Ensure floats in [0, 1]
            if len(color) == 3:  # Add alpha if missing
                color = np.append(color, 1.0)
            velocity = np.random.uniform(-0.02, 0.02, 3) * amplitude * 20
            particle = {
                "position": position,
                "size": size,
                "color": color,
                "velocity": velocity,
                "lifetime": 100  # Lifetime in frames
            }
            self.particles.append(particle)

    def update(self):
        """Update particle positions and remove out-of-bounds particles."""
        new_particles = []  # Collect particles that are still in bounds

        for particle in self.particles:
            particle["position"] += particle["velocity"]
            particle["lifetime"] -= 1  # Decrement lifetime

            # Check if the particle is within bounds
            if particle["lifetime"] > 0 and np.all(np.abs(particle["position"]) <= 0.9):
                new_particles.append(particle)


        # Replace the old particle list with the filtered one
        self.particles = new_particles

    def get_data(self):
        positions = np.array([p["position"] for p in self.particles])
        sizes = np.array([p["size"] for p in self.particles])
        colors = np.array([p["color"] for p in self.particles])
        return positions, sizes, colors


class ParticleCanvas(scene.SceneCanvas):
    def __init__(self):
        scene.SceneCanvas.__init__(self, keys="interactive", size=(800, 600), bgcolor="black")
        self.unfreeze()
        self.view = self.central_widget.add_view()
        self.view.camera = "arcball"

        self.particle_system = ParticleSystem()
        self.scatter = scene.visuals.Markers()
        self.view.add(self.scatter)

        self.timer = app.Timer(0.03, connect=self.update_particles, start=True)


    def update_particles(self, event):
        amplitude = visualization_data["amplitude"]
        dominant_note = visualization_data["dominant_note"]

        if visualization_data["decibels"] >= db_threshold and dominant_note != "N/A":
            self.particle_system.create_particles(amplitude, dominant_note)

        self.particle_system.update()
        positions, sizes, colors = self.particle_system.get_data()

        # Handle empty particle lists
        if len(positions) == 0 or len(sizes) == 0 or len(colors) == 0:
            positions = np.zeros((1, 3))  # Placeholder position
            sizes = np.zeros(1)          # Placeholder size
            colors = np.zeros((1, 4))    # Placeholder color (RGBA)

        try:
            self.scatter.set_data(
                pos=positions,
                size=sizes,
                edge_color=colors,
                face_color=colors
            )
        
        except ValueError as e:
            print(f"Error setting data: {e}")
            print(f"Positions: {positions}")
            print(f"Sizes: {sizes}")
            print(f"Colors: {colors}")


def main():
    global visualization_data
    stream = sd.InputStream(callback=audio_callback, samplerate=samplerate, channels=1, blocksize=block_size)
    stream.start()

    canvas = ParticleCanvas()
    canvas.show()

    app.run()

    stream.stop()

if __name__ == "__main__":
    main()
