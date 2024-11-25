import sounddevice as sd
import numpy as np
import pygame
import random
import math

# Parameters
samplerate = 44100  # Standard audio sample rate
duration = 0.1      # Duration per audio block in seconds
block_size = int(samplerate * duration)
num_particles = 100  # Number of particles
db_threshold = 50    # Decibel threshold for triggering effects

# Audio processing function
def process_audio(audio_block):
    """Process real-time audio block."""
    global visualization_data

    # Compute amplitude
    amplitude = np.abs(audio_block).mean()

    # Convert amplitude to decibels
    if amplitude > 0:
        decibels = 20 * np.log10(amplitude) + 100  # Normalize to positive range
    else:
        decibels = 0  # Silence case

    # Compute FFT for frequency analysis
    fft = np.fft.fft(audio_block)
    frequencies = np.fft.fftfreq(len(fft), 1 / samplerate)
    fft_magnitude = np.abs(fft[:len(fft) // 2])

    # Normalize FFT data for visualization
    fft_magnitude_normalized = fft_magnitude / np.max(fft_magnitude) if np.max(fft_magnitude) > 0 else fft_magnitude

    # Beat detection (simplistic: high energy in bass frequencies)
    beat = np.sum(fft_magnitude[:int(len(fft_magnitude) * 0.1)])  # Energy in the lower 10% of frequencies

    # Update data for visualization
    visualization_data = {
        "amplitude": amplitude,
        "fft": fft_magnitude_normalized,
        "frequencies": frequencies[:len(frequencies) // 2],
        "decibels": decibels,
        "beat": beat
    }


# Particle class
class Particle:
    def __init__(self):
        self.x = random.uniform(0, 800)
        self.y = random.uniform(0, 600)
        self.size = random.uniform(5, 15)
        self.color = (255, 255, 255)
        self.velocity = [random.uniform(-1, 1), random.uniform(-1, 1)]

    def move(self, amplitude, decibels):
        """Move the particle."""
        # Base speed for slow movement
        base_speed = 0.5
        speed = base_speed if decibels < db_threshold else base_speed + amplitude * 10  # Increased scaling factor
        self.x += self.velocity[0] * speed
        self.y += self.velocity[1] * speed

        # Wrap around the screen
        if self.x < 0 or self.x > 800:
            self.velocity[0] *= -1
        if self.y < 0 or self.y > 600:
            self.velocity[1] *= -1

    def apply_sound_effects(self, fft, beat):
        """Apply sound-driven dynamics."""
        # Change color based on frequency spectrum
        if len(fft) > 0:
            frequency_index = random.randint(0, len(fft) - 1)
            self.color = (
                int(fft[frequency_index] * 255),
                random.randint(50, 150),
                random.randint(100, 200)
            )
        # Change size based on beat
        self.size = max(5, beat / 100)

    def draw(self, screen):
        """Draw the particle on the screen."""
        pygame.draw.circle(screen, self.color, (int(self.x), int(self.y)), int(self.size))

    def check_collision(self, other):
        """Check and handle collision with another particle."""
        dx = self.x - other.x
        dy = self.y - other.y
        distance = math.sqrt(dx**2 + dy**2)

        # Check if particles are colliding
        if distance < self.size + other.size:
            # Resolve collision by swapping velocities
            self.velocity, other.velocity = other.velocity, self.velocity

            # Separate particles slightly to avoid sticking
            overlap = self.size + other.size - distance
            self.x += dx / distance * overlap / 2
            self.y += dy / distance * overlap / 2
            other.x -= dx / distance * overlap / 2
            other.y -= dy / distance * overlap / 2
