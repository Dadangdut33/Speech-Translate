import unittest
from tkinter import Tk

import os
import sys

toAdd = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(toAdd)

from speech_translate.components.custom.combobox import ComboboxTypeOnCustom  # noqa: E402


class TestComboboxTypeOnCustom(unittest.TestCase):
    def setUp(self):
        self.root = Tk()

    def tearDown(self):
        self.root.destroy()

    def test_initial_value_in_values(self):
        values = ["Value 1", "Value 2", "Value 3"]
        initial_value = "Value 2"
        cb = ComboboxTypeOnCustom(self.root, self.root, values, "1", "100", lambda x: None, initial_value)
        self.assertEqual(cb.get(), initial_value)
        self.assertEqual(str(cb.cget("state")), "readonly")

    def test_initial_value_is_custom(self):
        values = ["Value 1", "Value 2", "Value 3"]
        initial_value = "5"
        cb = ComboboxTypeOnCustom(self.root, self.root, values, "1", "100", lambda x: None, initial_value)
        self.assertEqual(cb.get(), initial_value)
        self.assertEqual(str(cb.cget("state")), "normal")

    def test_initial_value_not_a_digit(self):
        values = ["Value 1", "Value 2", "Value 3"]
        initial_value = "not a digit"
        with self.assertRaises(ValueError):
            ComboboxTypeOnCustom(self.root, self.root, values, "1", "100", lambda x: None, initial_value)

    def test_select_custom(self):
        values = ["Value 1", "Value 2", "Value 3"]
        initial_value = "5"
        cb = ComboboxTypeOnCustom(self.root, self.root, values, "1", "100", lambda x: None, initial_value)
        cb.set("Custom")
        cb.event_generate("<<ComboboxSelected>>")
        self.assertEqual(cb.get(), initial_value)
        self.assertEqual(str(cb.cget("state")), "normal")

    def test_select_not_custom(self):
        values = ["Value 1", "Value 2", "Value 3"]
        initial_value = "33"
        cb = ComboboxTypeOnCustom(self.root, self.root, values, "1", "100", lambda x: None, initial_value)
        cb.set("Value 1")
        cb.event_generate("<<ComboboxSelected>>")
        self.assertEqual(cb.get(), "Value 1")
        self.assertEqual(str(cb.cget("state")), "readonly")


unittest.main()
sys.path.remove(toAdd)
