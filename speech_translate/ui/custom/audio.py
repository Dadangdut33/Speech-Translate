from tkinter import Canvas


class AudioMeter(Canvas):
    """
    An audio meter that shows the loudness of the audio signal.
    
    The meter can be set to auto mode, where it will flash when the audio signal is above the threshold.
    
    This class extends the tkinter Canvas class.
    """
    def __init__(self, master, root, show_threshold: bool, v_min: float, v_max: float, **kwargs):
        super().__init__(master, **kwargs)

        self.root = root
        self.min = v_min
        self.max = v_max
        self.show_threshold = show_threshold
        self.db = 0
        self.threshold = 0.0
        self.running = False
        self.auto = False
        self.recording = False
        self.after_id = None
        self.disabled = False

    def set_disabled(self, disabled):
        self.disabled = disabled

    def set_db(self, db):
        self.db = db

    def set_max(self, v_max):
        self.max = v_max

    def set_min(self, v_min):
        self.min = v_min

    def set_threshold(self, threshold):
        self.threshold = threshold

    def set_auto(self, auto):
        self.auto = auto

    def set_recording(self, recording):
        self.recording = recording

    def start(self):
        if self.disabled:
            return

        self.running = True
        self.update_visual()

    def stop(self):
        if self.after_id:
            self.root.after_cancel(self.after_id)
        self.running = False

    def update_visual(self):
        if not self.auto:
            self.meter_update()
        else:
            self.meter_update_flash()

        if self.running:
            self.after_id = self.root.after(10, self.update_visual)

    def meter_update(self):
        # Map loudness to the canvas width
        loudness_percentage = (self.db - self.min) / (self.max - self.min)
        bar_width = int(self.winfo_width() * loudness_percentage)

        # Update the loudness bar
        self.bar_update(bar_width)

    def bar_update(self, bar_width):
        # Clear canvas and draw the loudness bar
        self.delete("all")
        self.create_rectangle(0, 0, bar_width, self.winfo_height(), fill="green", tags="loudness_bar")
        self.ruler_update()

    def ruler_update(self):
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

    def meter_update_flash(self):
        """
        When on auto mode we want it to just show flashing and only when its recording
        """
        try:
            if self.recording:
                self.flash()
            else:
                self.delete("all")
        except Exception:
            pass

    def flash(self):
        # Map loudness to the canvas width
        loudness_percentage = (self.db - self.min) / (self.max - self.min)
        bar_width = int(self.winfo_width() * loudness_percentage)

        # Update the loudness bar
        self.flash_bar(bar_width)

    def flash_bar(self, bar_width):
        # Clear canvas and draw the loudness bar
        self.delete("all")
        self.create_rectangle(0, 0, bar_width, self.winfo_height(), fill="green", tags="flash")
