import threading
import tkinter as tk


class AudioMeter(tk.Canvas):
    def __init__(self, master, show_threshold, min, max, **kwargs):
        super().__init__(master, **kwargs)

        self.chunk_size = 1024
        self.min = min
        self.max = max
        self.show_threshold = show_threshold
        self.db = 0
        self.threshold = 0

    def set_db(self, db):
        self.db = db

    def set_threshold(self, threshold):
        self.threshold = threshold

    def start(self):
        self.running = True
        self.update_thread = threading.Thread(target=self.update_meter)
        self.update_thread.daemon = True
        self.update_thread.start()

    def stop(self):
        self.running = False

    def update_meter(self):
        while self.running:
            # Map loudness to the canvas width
            loudness_percentage = (self.db - self.min) / (self.max - self.min)
            bar_width = int(self.winfo_width() * loudness_percentage)

            # Clear canvas and draw the loudness bar
            self.after(0, self.update_bar, bar_width)

    def update_bar(self, bar_width):
        # Clear canvas and draw the loudness bar
        self.delete("all")
        self.create_rectangle(0, 0, bar_width, self.winfo_height(), fill="green", tags="loudness_bar")
        self.draw_ruler()

    def draw_ruler(self):
        # Draw dB level markers. For every 5 db make long line and text, other than that make little line
        for db_level in range(int(self.min), int(self.max + 1)):
            marker_x = (db_level - self.min) / (self.max - self.min) * self.winfo_width()

            if self.show_threshold and db_level == int(self.threshold):
                self.create_line(marker_x, 0, marker_x, self.winfo_height(), fill="red", tags="ruler", width=1)

            if db_level % 5 == 0:
                self.create_line(marker_x, 0, marker_x, self.winfo_height() / 4, fill="black", tags="ruler")
                # if last or first no need to draw text
                if db_level != self.min and db_level != self.max:
                    self.create_text(marker_x, self.winfo_height() / 2, text=f"{db_level}", fill="black", tags="ruler")
            else:
                self.create_line(marker_x, 0, marker_x, self.winfo_height() / 5, fill="black", tags="ruler")
