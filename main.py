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
from proglog import ProgressBarLogger


class ScreenRecorder:
    def __init__(self):
        self.root = ThemedTk(theme="black", themebg=True)
        self.start_stop_button = None
        self.state_label = ttk.Label(self.root)
        self.progress_bar = ttk.Progressbar(self.root, orient="horizontal")
        self.setup_gui()

        self.recording = False
        self.out = None
        self.video_clip = None
        self.start_time = None
        self.duration = None
        self.bar_logger = MyBarLogger(self.progress_bar)

    def setup_gui(self):
        self.root.title("Screen Recorder")

        self.start_stop_button = ttk.Button(
            self.root,
            text="Start Recording",
            command=self.start_recording,
            padding=(9, 0),
        )
        self.start_stop_button.grid(row=0, column=0, padx=10, pady=10)

    def start_recording(self):
        self.start_time = datetime.now()
        self.start_stop_button.config(
            text="Stop Recording", command=self.stop_recording
        )
        self.root.iconify()  # Minimize the window
        threading.Thread(target=self.record_screen, daemon=True).start()
        threading.Thread(target=self.record_system_audio, daemon=True).start()

        self.state_label.config(text="Recording...")
        self.state_label.grid(row=2, column=0, pady=(0, 5))
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

    def adjust_video_speed(self, target_duration):
        # Load the original video clip
        self.video_clip = VideoFileClip("temp_output.mp4")

        # Calculate the speed factor to achieve the target duration
        speed_factor = self.video_clip.duration / target_duration

        # Adjust the video speed
        self.video_clip = self.video_clip.fx(vfx.speedx, speed_factor)

    def choose_file_path_and_save(self):
        output_path = filedialog.asksaveasfilename(
            defaultextension=".mp4", filetypes=[("MP4 files", "*.mp4")]
        )

        self.state_label.config(text="Processing...")
        self.state_label.grid(row=2, column=0, pady=(0, 5))
        self.progress_bar.grid(row=1, column=0, pady=(0, 5))

        self.adjust_video_speed(self.duration)

        audio_clip = AudioFileClip("temp_output.mp3")
        self.video_clip = self.video_clip.set_audio(audio_clip)
        self.video_clip.write_videofile(
            "final_output.mp4", preset="ultrafast", logger=self.bar_logger
        )

        self.video_clip.close()
        audio_clip.close()

        for filepath in [
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

        self.progress_bar.grid_forget()
        self.state_label.config(text="Done!")
        self.root.after(3000, self.state_label.grid_forget)


class MyBarLogger(ProgressBarLogger):
    def __init__(self, progress_bar):
        super().__init__()
        self.progress_bar = progress_bar

    def bars_callback(self, bar, attr, value, old_value=None):
        # Every time the logger progress is updated, this function is called
        percentage = (value / self.bars[bar]["total"]) * 100
        self.progress_bar.config(value=percentage)


if __name__ == "__main__":
    recorder = ScreenRecorder()
    recorder.root.mainloop()
