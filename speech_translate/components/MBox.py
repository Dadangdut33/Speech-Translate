##  Styles:
##  0 : info
##  1 : warning
##  2 : error
##  3 : Yes No
from tkinter import Tk, messagebox
from typing import Literal


def Mbox(title: str, text: str, style: Literal[0, 1, 2, 3], parent = None):
    """Message Box, made simpler
    ##  Styles:
    ##  0 : info
    ##  1 : warning
    ##  2 : error
    ##  3 : Yes No
    """
    if style == 0:
        return messagebox.showinfo(title, text, parent=parent)  # Return ok x same as ok
    elif style == 1:
        return messagebox.showwarning(title, text, parent=parent)  # Return ok x same as ok
    elif style == 2:
        return messagebox.showerror(title, text, parent=parent)  # Return ok x same as ok
    elif style == 3:
        return messagebox.askyesno(title, text, parent=parent)  # Return True False, x can't be clicked


# Testing
if __name__ == "__main__":
    root = Tk()

    # -----------------
    Mbox("Info", "Info no parent", 0)
    Mbox("Warning", "Warning no parent", 1)
    Mbox("Error", "Error no parent", 2)
    print(Mbox("Yes No", "Yes No no parent", 3))

    # -----------------
    Mbox("Info", "Info with parent", 0, parent=root)
    Mbox("Warning", "Warning with parent", 1, parent=root)
    Mbox("Error", "Error with parent", 2, parent=root)
    print(Mbox("Yes No", "Yes No with parent", 3, parent=root))
    
    
    root.destroy()
