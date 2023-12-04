import unittest
from unittest.mock import MagicMock
import os
import sys

toAdd = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(toAdd)

from speech_translate.ui.custom.audio import AudioMeter  # noqa: E402


class TestAudioMeter(unittest.TestCase):
    def setUp(self):
        self.root = MagicMock()
        self.master = MagicMock()
        self.kwargs = {"width": 100, "height": 100}
        self.audio_meter = AudioMeter(self.master, self.root, True, -60, 0, **self.kwargs)

    def test_set_db(self):
        self.audio_meter.set_db(-30)
        self.assertEqual(self.audio_meter.db, -30)

    def test_set_max(self):
        self.audio_meter.set_max(6)
        self.assertEqual(self.audio_meter.max, 6)

    def test_set_min(self):
        self.audio_meter.set_min(-12)
        self.assertEqual(self.audio_meter.min, -12)

    def test_set_threshold(self):
        self.audio_meter.set_threshold(-20)
        self.assertEqual(self.audio_meter.threshold, -20)

    def test_set_auto(self):
        self.audio_meter.set_auto(True)
        self.assertEqual(self.audio_meter.auto, True)

    def test_set_recording(self):
        self.audio_meter.set_recording(True)
        self.assertEqual(self.audio_meter.recording, True)

    def test_start(self):
        self.audio_meter.running = False
        self.audio_meter.update_visual = MagicMock()
        self.audio_meter.start()
        self.assertEqual(self.audio_meter.running, True)
        self.audio_meter.update_visual.assert_called_once()

    def test_stop(self):
        self.audio_meter.after_id = MagicMock()
        self.audio_meter.stop()
        self.assertEqual(self.audio_meter.running, False)
        self.audio_meter.root.after_cancel.assert_called_once_with(self.audio_meter.after_id)

    def test_meter_update(self):
        self.audio_meter.db = -30
        self.audio_meter.min = -60
        self.audio_meter.max = 0
        self.audio_meter.winfo_width = MagicMock(return_value=100)
        self.audio_meter.bar_update = MagicMock()
        self.audio_meter.meter_update()
        self.audio_meter.bar_update.assert_called_once_with(50)

    def test_bar_update(self):
        self.audio_meter.winfo_height = MagicMock(return_value=100)
        self.audio_meter.delete = MagicMock()
        self.audio_meter.create_rectangle = MagicMock()
        self.audio_meter.ruler_update = MagicMock()
        self.audio_meter.bar_update(50)
        self.audio_meter.delete.assert_called_once_with("all")
        self.audio_meter.create_rectangle.assert_called_once_with(0, 0, 50, 100, fill="green", tags="loudness_bar")
        self.audio_meter.ruler_update.assert_called_once()

    def test_ruler_update(self):
        self.audio_meter.min = -60
        self.audio_meter.max = 0
        self.audio_meter.winfo_width = MagicMock(return_value=100)
        self.audio_meter.winfo_height = MagicMock(return_value=100)
        self.audio_meter.show_threshold = True
        self.audio_meter.threshold = -20
        self.audio_meter.create_line = MagicMock()
        self.audio_meter.create_text = MagicMock()
        self.audio_meter.ruler_update()
        # value below is based on the min and max values
        self.assertEqual(self.audio_meter.create_line.call_count, 62)  # 62 times create_line is called
        self.assertEqual(self.audio_meter.create_text.call_count, 11)  # 11 times create_text is called

    def test_meter_update_flash(self):
        self.audio_meter.auto = True
        self.audio_meter.recording = True
        self.audio_meter.flash = MagicMock()
        self.audio_meter.meter_update_flash()
        self.audio_meter.flash.assert_called_once()

    def test_flash(self):
        self.audio_meter.db = -30
        self.audio_meter.min = -60
        self.audio_meter.max = 0
        self.audio_meter.winfo_width = MagicMock(return_value=100)
        self.audio_meter.delete = MagicMock()
        self.audio_meter.create_rectangle = MagicMock()
        self.audio_meter.flash_bar = MagicMock()
        self.audio_meter.flash()
        self.audio_meter.flash_bar.assert_called_once_with(50)

    def test_flash_bar(self):
        self.audio_meter.winfo_height = MagicMock(return_value=100)
        self.audio_meter.delete = MagicMock()
        self.audio_meter.create_rectangle = MagicMock()
        self.audio_meter.flash_bar(50)
        self.audio_meter.delete.assert_called_once_with("all")
        self.audio_meter.create_rectangle.assert_called_once_with(0, 0, 50, 100, fill="green", tags="flash")


unittest.main()
sys.path.remove(toAdd)
