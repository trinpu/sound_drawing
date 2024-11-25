import sounddevice as sd
import numpy as np
import pygame
from PIL import Image, ImageDraw

print(sd.query_devices(1))


# Parameters
samplerate = 44100  # Standard audio sample rate
duration = 0.1      # Duration per audio block in seconds
block_size = int(samplerate * duration)

# Global variable to share visualization data
visualization_data = {"amplitude": 0, "fft": [], "frequencies": []}

# Real-time audio callback
def audio_callback(indata, frames, time, status):
    """Callback function for audio input."""
    if status:
        print(status)
    audio_block = indata[:, 0]  # Extract single channel
    process_audio(audio_block)  # Pass to processing layer

# Audio processing function
def process_audio(audio_block):
    """Process real-time audio block."""
    global visualization_data

    # Compute amplitude
    amplitude = np.abs(audio_block).mean()

    # Compute FFT for frequency analysis
    fft = np.fft.fft(audio_block)
    frequencies = np.fft.fftfreq(len(fft), 1 / samplerate)
    fft_magnitude = np.abs(fft[:len(fft) // 2])

    # Normalize FFT data for visualization
    fft_magnitude_normalized = fft_magnitude / np.max(fft_magnitude) if np.max(fft_magnitude) > 0 else fft_magnitude

    # Update data for visualization
    visualization_data = {
        "amplitude": amplitude,
        "fft": fft_magnitude_normalized,
        "frequencies": frequencies[:len(frequencies) // 2]
    }

# Generate a waveform image
def generate_waveform_image(audio_block):
    """Create an image of the waveform."""
    img = Image.new('RGB', (800, 600), color=(0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Normalize audio block for plotting
    if np.max(np.abs(audio_block)) > 0:
        normalized_audio = audio_block / np.max(np.abs(audio_block))
    else:
        normalized_audio = audio_block

    # Map the waveform data to the image canvas
    num_samples = len(normalized_audio)
    canvas_width, canvas_height = img.size
    midline = canvas_height // 2
    x_step = canvas_width / num_samples  # Step size for evenly distributing points

    for i in range(num_samples - 1):
        x1 = int(i * x_step)
        y1 = int(midline + normalized_audio[i] * (canvas_height // 3))
        x2 = int((i + 1) * x_step)
        y2 = int(midline + normalized_audio[i + 1] * (canvas_height // 3))
        draw.line([(x1, y1), (x2, y2)], fill=(0, 255, 0), width=2)

    return img

# Visualization rendering function
def render_visualization(screen):
    """Render visuals based on real-time audio data."""
    screen.fill((0, 0, 0))  # Clear screen

    # Render FFT bars
    if len(visualization_data["fft"]) > 0:
        fft = visualization_data["fft"]
        bar_width = 800 // len(fft)
        for i, magnitude in enumerate(fft):
            bar_height = magnitude * 300  # Scale for visualization
            pygame.draw.rect(
                screen,
                (0, 255, 255),
                (
                    int(i * bar_width),
                    int(600 - bar_height),
                    int(bar_width),
                    int(bar_height)
                )
            )

    # Render waveform image
    if len(visualization_data["fft"]) > 0:  # Use FFT as proxy for audio block presence
        audio_block = visualization_data["fft"]
        img = generate_waveform_image(audio_block)
        mode = img.mode
        size = img.size
        data = img.tobytes()
        surface = pygame.image.fromstring(data, size, mode)
        screen.blit(surface, (0, 0))

    pygame.display.flip()


# Main function
def main():
    global visualization_data

    # Initialize Pygame
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    clock = pygame.time.Clock()

    # Start audio stream
    stream = sd.InputStream(callback=audio_callback, samplerate=samplerate, channels=1, device=1, blocksize=block_size)
    stream.start()

    # Main loop
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # Render the visualization
        render_visualization(screen)
        clock.tick(30)  # Limit to 30 FPS

    # Clean up
    stream.stop()
    stream.close()
    pygame.quit()

# Entry point
if __name__ == "__main__":
    main()
