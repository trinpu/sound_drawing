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