import numpy as np
import cv2
from PIL import ImageGrab
from tkinter import filedialog
from tkinter import ttk
from ttkthemes import ThemedTk
import threading
import os
from datetime import datetime
from moviepy.editor import VideoFileClip, AudioFileClip, vfx
import sounddevice as sd
import soundfile as sf
import time


def adjust_video_speed(original_path, target_duration):
    # Load the original video clip
    clip = VideoFileClip(original_path)

    # Calculate the speed factor to achieve the target duration
    speed_factor = clip.duration / target_duration

    # Adjust the video speed
    adjusted_clip = clip.fx(vfx.speedx, speed_factor)

    # Write the adjusted video clip to a new file
    output_path = "speed_adjusted_output.mp4"
    adjusted_clip.write_videofile(output_path)


class ScreenRecorder:
    def __init__(self):
        self.root = ThemedTk(theme="black", themebg=True)
        self.start_stop_button = None
        self.state_label = None
        self.setup_gui()
        self.recording = False
        self.out = None
        self.start_time = None
        self.duration = None

    def setup_gui(self):
        self.root.title("Screen Recorder")

        self.start_stop_button = ttk.Button(
            self.root, text="Start Recording", command=self.start_recording
        )
        self.start_stop_button.pack(padx=10, pady=10)

        self.state_label = ttk.Label(self.root)

    def start_recording(self):
        self.start_time = datetime.now()
        self.start_stop_button.config(
            text="Stop Recording", command=self.stop_recording
        )
        self.root.iconify()  # Minimize the window
        threading.Thread(target=self.record_screen, daemon=True).start()
        threading.Thread(target=self.record_system_audio, daemon=True).start()

        self.state_label.config(text="Recording...")
        self.state_label.pack(pady=(0, 5))
        self.root.after(3000, self.update_timer)

    def update_timer(self):
        mins, secs = divmod(int((datetime.now() - self.start_time).total_seconds()), 60)
        self.state_label.config(text=f"{mins:02d}:{secs:02d}")
        if self.recording:
            self.state_label.after(1000, self.update_timer)

    def stop_recording(self):
        self.duration = (datetime.now() - self.start_time).total_seconds()
        self.recording = False
        self.root.deiconify()  # Restore the window

    def record_screen(self):
        self.recording = True
        screen_size = (self.root.winfo_screenwidth(), self.root.winfo_screenheight())
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        # Temporarily create a VideoWriter object with a dummy path
        self.out = cv2.VideoWriter("temp_output.mp4", fourcc, 20.0, screen_size)

        print("Recording Started...")
        while self.recording:
            img = ImageGrab.grab(bbox=(0, 0, screen_size[0], screen_size[1]))
            img_np = np.array(img)
            frame = cv2.cvtColor(img_np, cv2.COLOR_BGR2RGB)
            self.out.write(frame)

        self.out.release()
        cv2.destroyAllWindows()
        print("Recording Stopped.")
        self.choose_file_path_and_save()
        self.start_stop_button.config(
            text="Start Recording", command=self.start_recording
        )

    def record_system_audio(self):
        fs = 44100
        seconds = 3600

        myrecording = sd.rec(seconds * fs, samplerate=fs, channels=2, device=2)

        while self.recording:
            time.sleep(0.1)

        write_file = "temp_output.mp3"
        sf.write(write_file, myrecording[: int(self.duration * fs)], fs)

    def choose_file_path_and_save(self):
        output_path = filedialog.asksaveasfilename(
            defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4")]
        )

        self.state_label.config(text="Processing...")
        self.state_label.pack(pady=(0, 5))

        adjust_video_speed("temp_output.mp4", self.duration)

        video_clip = VideoFileClip("speed_adjusted_output.mp4")
        audio_clip = AudioFileClip("temp_output.mp3")
        video_clip = video_clip.set_audio(audio_clip)
        video_clip.write_videofile("final_output.mp4")

        video_clip.close()
        audio_clip.close()

        for filepath in [
            "speed_adjusted_output.mp4",
            "temp_output.mp3",
            "temp_output.mp4",
        ]:
            if filepath != output_path:
                os.remove(filepath)

        if output_path:
            try:
                os.rename("final_output.mp4", output_path)
            except FileExistsError:
                os.replace("final_output.mp4", output_path)

            print("Video saved to:", output_path)
        else:
            print("No file path selected.")

        self.state_label.config(text="Done!")
        self.root.after(3000, self.state_label.pack_forget)


if __name__ == "__main__":
    recorder = ScreenRecorder()
    recorder.root.mainloop()
