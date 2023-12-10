import os
import sys
import tkinter as tk

toAdd = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(toAdd)

from speech_translate.ui.custom.combobox import (  # pylint: disable=wrong-import-position
    CategorizedComboBox,
    ComboboxTypeOnCustom,
)

root = tk.Tk()
try:
    root.title("ComboBox Example")

    values = ["Option 1", "Option 2", "Option 3"]
    INITIAL = "Option 2"
    # initial_value = "33"
    # initial_value = "test"
    editable_combo = ComboboxTypeOnCustom(root, root, values, "1", "25", print, INITIAL)
    editable_combo.pack(pady=10)

    categories = {
        "Fruits": ["Apple", "Banana", "Orange"],
        "Vegetables": ["Carrot", "Broccoli", "Lettuce"],
        "Colors": ["Red", "Green", "Blue"],
        "no category 1": [],
        "no category 2": [],
        "no category 3": []
    }
    categorize_combo = CategorizedComboBox(root, root, categories, print)
    categorize_combo.pack(pady=10)

    root.mainloop()
except KeyboardInterrupt:
    root.destroy()

sys.path.remove(toAdd)
