import tkinter as tk
import os
import sys

toAdd = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(toAdd)

from speech_translate.components.custom.combobox import ComboboxTypeOnCustom, CategorizedComboBox  # noqa: E402

root = tk.Tk()
try:
    root.title("ComboBox Example")

    values = ["Option 1", "Option 2", "Option 3"]
    initial_value = "Option 2"
    # initial_value = "33"
    # initial_value = "test"
    editable_combo = ComboboxTypeOnCustom(root, root, values, "1", "25", lambda x: print(x), initial_value)
    editable_combo.pack(pady=10)

    categories = {
        "Fruits": ["Apple", "Banana", "Orange"],
        "Vegetables": ["Carrot", "Broccoli", "Lettuce"],
        "Colors": ["Red", "Green", "Blue"],
        "no category 1": [],
        "no category 2": [],
        "no category 3": []
    }
    categorize_combo = CategorizedComboBox(root, root, categories, lambda x: print(x))
    categorize_combo.pack(pady=10)

    root.mainloop()
except KeyboardInterrupt:
    root.destroy()

sys.path.remove(toAdd)
