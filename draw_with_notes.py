import numpy as np
import sounddevice as sd
from vispy import app, visuals, scene
import random

# Parameters
sample_rates = {'desktop': 44100, 'raspberry': 2250}  # Selector based on device
sample_rate = sample_rates["desktop"] 
duration = 0.2                                         # Increased duration per audio block
block_size = int(sample_rate * duration)
db_threshold = 50    # Decibel threshold for triggering effects
visualization_data = {"amplitude": 0, "fft": [], "frequencies": [], "dominant_note": "N/A"}


# Note colors
note_to_color = {
    "C": (0.6, 0.6, 1.0, 1.0),    # Soft blue
    "C#": (0.8, 0.6, 1.0, 1.0),   # Lavender
    "D": (1.0, 0.8, 1.0, 1.0),    # Light pink
    "D#": (1.0, 0.6, 0.8, 1.0),   # Rosy pink
    "E": (1.0, 0.6, 0.6, 1.0),    # Warm red-pink
    "F": (1.0, 0.8, 0.6, 1.0),    # Peach
    "F#": (1.0, 1.0, 0.8, 1.0),   # Warm white
    "G": (0.8, 1.0, 0.8, 1.0),    # Pale green
    "G#": (0.6, 1.0, 0.8, 1.0),   # Aqua-mint
    "A": (0.6, 1.0, 1.0, 1.0),    # Cyan
    "A#": (0.6, 0.8, 1.0, 1.0),   # Sky blue
    "B": (0.8, 0.6, 1.0, 1.0),    # Violet
}


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
    frequencies = np.fft.fftfreq(len(fft), 1 / sample_rate)
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

        # Default to white if the note is unrecognized
        color = note_to_color.get(dominant_note, (1.0, 1.0, 1.0, 1.0))

        for _ in range(5):  # Create up to 5 particles per note
            position = np.random.uniform(-1, 1, 3)
            size = np.random.randint(1, max(12, amplitude * 80))
            velocity = np.random.uniform(-0.05, 0.05, 3) * amplitude * 30
            particle = {
                "position": position,
                "size": size,
                "color": np.array(color, dtype=np.float32),  # Use note color
                "velocity": velocity,
                "lifetime": 15  # Lifetime in frames
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

        screen_size = {'laptop': (900, 900), 'projector': (3000,1500)}
        scene.SceneCanvas.__init__(self, keys="interactive", size=screen_size['laptop'], bgcolor="black")
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

## Alternative particle canvas - connecting 8% of particles with lines
## Feels a bit distracting...

# class ParticleCanvas(scene.SceneCanvas):
#     def __init__(self):
#         screen_size = {'laptop': (900, 900), 'projector': (3000,1500)}
#         scene.SceneCanvas.__init__(self, keys="interactive", size=screen_size['laptop'], bgcolor="black")
#         self.unfreeze()
#         self.view = self.central_widget.add_view()
#         self.view.camera = "arcball"

#         self.particle_system = ParticleSystem()
#         self.scatter = scene.visuals.Markers()
#         self.view.add(self.scatter)

#         # Add a Line visual for connecting particles
#         self.lines = scene.visuals.Line(parent=self.view.scene, color='white', width=2)

#         self.timer = app.Timer(0.03, connect=self.update_particles, start=True)

#     def update_particles(self, event):
#         amplitude = visualization_data["amplitude"]
#         dominant_note = visualization_data["dominant_note"]

#         if visualization_data["decibels"] >= db_threshold and dominant_note != "N/A":
#             self.particle_system.create_particles(amplitude, dominant_note)

#         self.particle_system.update()
#         positions, sizes, colors = self.particle_system.get_data()

#         # Handle empty particle lists
#         if len(positions) == 0 or len(sizes) == 0 or len(colors) == 0:
#             positions = np.zeros((1, 3))  # Placeholder position
#             sizes = np.zeros(1)          # Placeholder size
#             colors = np.zeros((1, 4))    # Placeholder color (RGBA)

#         # Update the scatter plot for particles
#         try:
#             self.scatter.set_data(
#                 pos=positions,
#                 size=sizes,
#                 edge_color=colors,
#                 face_color=colors
#             )
#         except ValueError as e:
#             print(f"Error setting data: {e}")
#             print(f"Positions: {positions}")
#             print(f"Sizes: {sizes}")
#             print(f"Colors: {colors}")

#         # Update the line connecting particles
#         if len(positions) > 1:
#             # Determine number of connections (30% of particles)
#             num_connections = int(len(positions) * 0.08)
            
#             # Randomly select unique pairs of indices
#             random_indices = np.random.choice(len(positions), size=(num_connections, 2), replace=False)
            
#             # Create line positions from the random pairs
#             lines_positions = positions[random_indices.flatten()]
            
#             # Update the line visual
#             self.lines.set_data(pos=lines_positions, color='grey', width=0.5)


def main():
    global visualization_data
    stream = sd.InputStream(callback=audio_callback, samplerate=sample_rate, channels=1, blocksize=block_size)
    stream.start()

    canvas = ParticleCanvas()
    canvas.show()

    app.run()

    stream.stop()

if __name__ == "__main__":
    main()
