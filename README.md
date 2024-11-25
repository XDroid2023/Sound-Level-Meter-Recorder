# Sound Level Meter

A simple desktop application that measures and displays the current sound level from your microphone in real-time.

## Features
- Real-time sound level monitoring
- Visual meter display
- Color-coded levels (green for low, yellow for medium, red for high)
- Simple and clean interface

## Requirements
- Python 3.7+
- sounddevice
- numpy

## Installation

1. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python sound_meter.py
```

The application will open a window showing the current sound level from your microphone. The meter will update in real-time and change colors based on the sound intensity:
- Green: Low level (< 30 dB)
- Yellow: Medium level (30-60 dB)
- Red: High level (> 60 dB)

## Note
Make sure your microphone is properly connected and enabled on your system.
