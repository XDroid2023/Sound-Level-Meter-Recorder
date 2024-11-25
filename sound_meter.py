import customtkinter as ctk
import sounddevice as sd
import numpy as np
from threading import Thread
import time
from PIL import Image, ImageDraw
import os
import soundfile as sf
from datetime import datetime

class SoundLevelMeter:
    def __init__(self):
        # Set theme and color scheme
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # Create main window
        self.root = ctk.CTk()
        self.root.title("Professional Sound Level Meter")
        self.root.geometry("800x500")
        self.root.resizable(False, False)
        
        # Create main frame
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="Sound Level Monitor",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=(0, 20))
        
        # Create frames for different sections
        self.meter_frame = ctk.CTkFrame(self.main_frame)
        self.meter_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Current level display
        self.level_frame = ctk.CTkFrame(self.meter_frame)
        self.level_frame.pack(side="left", padx=(0, 20))
        
        self.level_label = ctk.CTkLabel(
            self.level_frame,
            text="Current Level",
            font=ctk.CTkFont(size=14)
        )
        self.level_label.pack()
        
        self.level_value = ctk.CTkLabel(
            self.level_frame,
            text="0 dB",
            font=ctk.CTkFont(size=36, weight="bold")
        )
        self.level_value.pack()
        
        # Peak level display
        self.peak_frame = ctk.CTkFrame(self.meter_frame)
        self.peak_frame.pack(side="right")
        
        self.peak_label = ctk.CTkLabel(
            self.peak_frame,
            text="Peak Level",
            font=ctk.CTkFont(size=14)
        )
        self.peak_label.pack()
        
        self.peak_value = ctk.CTkLabel(
            self.peak_frame,
            text="0 dB",
            font=ctk.CTkFont(size=36, weight="bold")
        )
        self.peak_value.pack()
        
        # Progress bar frame
        self.progress_frame = ctk.CTkFrame(self.main_frame)
        self.progress_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        # Create custom meter canvas
        self.meter_canvas = ctk.CTkCanvas(
            self.progress_frame,
            width=740,
            height=60,
            bg='#2b2b2b',
            highlightthickness=0
        )
        self.meter_canvas.pack(pady=10)
        
        # Level indicators
        self.indicators_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.indicators_frame.pack(fill="x", padx=20)
        
        levels = ["Quiet", "Normal", "Loud"]
        colors = ["#4CAF50", "#FFC107", "#F44336"]
        
        for level, color in zip(levels, colors):
            indicator = ctk.CTkFrame(self.indicators_frame, fg_color="transparent")
            indicator.pack(side="left", expand=True)
            
            dot = ctk.CTkLabel(
                indicator,
                text="●",
                font=ctk.CTkFont(size=16),
                text_color=color
            )
            dot.pack(side="left", padx=5)
            
            label = ctk.CTkLabel(
                indicator,
                text=level,
                font=ctk.CTkFont(size=12)
            )
            label.pack(side="left")
        
        # Recording controls
        self.recording_frame = ctk.CTkFrame(self.main_frame)
        self.recording_frame.pack(fill="x", padx=20, pady=(20, 0))
        
        self.record_button = ctk.CTkButton(
            self.recording_frame,
            text="Start Recording",
            command=self.toggle_recording,
            width=200,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.record_button.pack(side="left", padx=(0, 10))
        
        self.recording_status = ctk.CTkLabel(
            self.recording_frame,
            text="Not Recording",
            font=ctk.CTkFont(size=14),
            text_color="#666666"
        )
        self.recording_status.pack(side="left", padx=10)
        
        self.recording_time = ctk.CTkLabel(
            self.recording_frame,
            text="00:00",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.recording_time.pack(side="right", padx=10)
        
        # Initialize audio parameters
        self.samplerate = 44100
        self.channels = 1
        self.blocksize = 1024
        
        # Initialize recording variables
        self.is_recording = False
        self.recorded_frames = []
        self.recording_start_time = None
        self.peak_during_recording = 0
        
        # Initialize audio input
        self.stream = sd.InputStream(
            callback=self.audio_callback,
            channels=self.channels,
            samplerate=self.samplerate,
            blocksize=self.blocksize
        )
        
        self.running = True
        self.level = 0
        self.peak_level = 0
        
        # Create recordings directory if it doesn't exist
        os.makedirs("recordings", exist_ok=True)
        
        # Start monitoring in a separate thread
        self.monitor_thread = Thread(target=self.update_display)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def audio_callback(self, indata, frames, time, status):
        volume_norm = np.linalg.norm(indata) * 10
        self.level = int(volume_norm)
        self.peak_level = max(self.peak_level, self.level)
        
        if self.is_recording:
            self.recorded_frames.append(indata.copy())
            self.peak_during_recording = max(self.peak_during_recording, self.level)
    
    def toggle_recording(self):
        if not self.is_recording:
            # Start recording
            self.is_recording = True
            self.recorded_frames = []
            self.recording_start_time = datetime.now()
            self.peak_during_recording = 0
            self.record_button.configure(
                text="Stop Recording",
                fg_color="#F44336",
                hover_color="#D32F2F"
            )
            self.recording_status.configure(
                text="Recording...",
                text_color="#F44336"
            )
        else:
            # Stop recording
            self.is_recording = False
            self.save_recording()
            self.record_button.configure(
                text="Start Recording",
                fg_color="#1f538d",
                hover_color="#14375e"
            )
            self.recording_status.configure(
                text="Not Recording",
                text_color="#666666"
            )
            self.recording_time.configure(text="00:00")
    
    def save_recording(self):
        if not self.recorded_frames:
            return
            
        # Convert list of frames to numpy array
        recording = np.concatenate(self.recorded_frames, axis=0)
        
        # Generate filename with metadata
        timestamp = self.recording_start_time.strftime("%Y%m%d_%H%M%S")
        duration = (datetime.now() - self.recording_start_time).seconds
        peak_db = int(self.peak_during_recording)
        
        # Save as WAV
        filename = f"recordings/recording_{timestamp}_peak{peak_db}db_dur{duration}s.wav"
        sf.write(filename, recording, self.samplerate)
        
        # Update status
        self.recording_status.configure(
            text=f"Saved as: {os.path.basename(filename)}",
            text_color="#4CAF50"
        )
    
    def get_color(self, level):
        if level < 30:
            return "#4CAF50"  # Green
        elif level < 60:
            return "#FFC107"  # Yellow
        else:
            return "#F44336"  # Red
    
    def format_time(self, seconds):
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    def update_display(self):
        while self.running:
            if hasattr(self, 'level'):
                try:
                    # Update level display
                    self.level_value.configure(text=f"{self.level} dB")
                    self.peak_value.configure(text=f"{self.peak_level} dB")
                    
                    # Update recording time if recording
                    if self.is_recording and self.recording_start_time:
                        duration = int((datetime.now() - self.recording_start_time).total_seconds())
                        self.recording_time.configure(text=self.format_time(duration))
                    
                    # Update meter
                    self.meter_canvas.delete("all")
                    
                    # Draw background segments
                    segment_width = 24
                    gap = 2
                    total_segments = 30
                    
                    for i in range(total_segments):
                        x1 = i * (segment_width + gap)
                        x2 = x1 + segment_width
                        
                        # Calculate color based on position
                        if i < 10:
                            color = "#4CAF50"  # Green
                        elif i < 20:
                            color = "#FFC107"  # Yellow
                        else:
                            color = "#F44336"  # Red
                        
                        # Draw background segment
                        self.meter_canvas.create_rectangle(
                            x1, 10, x2, 50,
                            fill="#3b3b3b",
                            width=0
                        )
                        
                        # Draw active segment if level is high enough
                        if i <= (self.level / 3):  # Scale level to segments
                            self.meter_canvas.create_rectangle(
                                x1, 10, x2, 50,
                                fill=color,
                                width=0
                            )
                except Exception as e:
                    pass  # Ignore any GUI update errors
            
            time.sleep(0.05)
    
    def run(self):
        with self.stream:
            self.root.mainloop()
        
        self.running = False

if __name__ == "__main__":
    app = SoundLevelMeter()
    app.run()
