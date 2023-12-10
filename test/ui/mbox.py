import os
import sys
from tkinter import Tk

toAdd = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(toAdd)

from speech_translate.ui.custom.message import mbox  # pylint: disable=wrong-import-position

root = Tk()

# -----------------
mbox("Info", "Info no parent", 0)
mbox("Warning", "Warning no parent", 1)
mbox("Error", "Error no parent", 2)
print(mbox("Yes No", "Yes No no parent", 3))

# -----------------
mbox("Info", "Info with parent", 0, parent=root)
mbox("Warning", "Warning with parent", 1, parent=root)
mbox("Error", "Error with parent", 2, parent=root)
print(mbox("Yes No", "Yes No with parent", 3, parent=root))

root.destroy()

sys.path.remove(toAdd)
