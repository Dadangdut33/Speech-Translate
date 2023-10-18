from tkinter import ttk, Tk, Toplevel, Menu
from typing import List, Union


class ComboboxTypeOnCustom(ttk.Combobox):
    """
    Combobox that allows to type on custom value
    Designed for integer values
    """
    def __init__(
        self, root: Union[Tk, Toplevel], master, values: List[str], vmin: str, vmax: str, save_func, initial_value: str,
        **kwargs
    ):
        super().__init__(master, values=values.copy() + ["Custom"], **kwargs)
        self.root = root
        self.values = values
        self.vmin = vmin
        self.vmax = vmax
        self.prev = None
        self.save_func = save_func
        self.verify_after = None

        if str(initial_value) in values:
            # selection is in cb -> readonly
            if isinstance(initial_value, str) and not initial_value.isdigit():
                self.prev = vmin
            else:
                self.prev = str(initial_value)

            self.set(initial_value)
            self.configure(state='readonly')
        else:
            if isinstance(initial_value, str) and not initial_value.isdigit():
                raise ValueError("Initial value must be a string of digit")
            elif isinstance(initial_value, int):
                initial_value = str(initial_value)

            # custom
            self.prev = initial_value
            self.set(initial_value)
            self.configure(state='normal')

        self.prev_state = str(self.cget('state'))
        # Bind the select event to the on_select function
        self.bind("<<ComboboxSelected>>", self.on_select)

        # Bind the KeyRelease event to capture text input
        self.bind("<KeyRelease>", self.on_key_release)

    def on_select(self, event):
        selected_item = self.get()
        if selected_item == "Custom":
            self.set(self.prev)
            self.save_func(self.prev)
            self.configure(state='normal')
        else:
            if selected_item.isdigit():
                self.prev = selected_item

            self.set(selected_item)
            self.save_func(selected_item)
            self.configure(state='readonly')

    def on_key_release(self, event):
        typed_text = self.get()
        if self.verify_after:
            self.root.after_cancel(self.verify_after)

        self.verify_after = self.root.after(200, self.verify_w_delay, typed_text)

    def verify_w_delay(self, typed_text: str):
        if typed_text.isdigit():
            value = int(typed_text)
            if value < int(self.vmin):
                self.set(self.vmin)
                self.prev = self.vmin
            elif value > int(self.vmax):
                self.set(self.vmax)
                self.prev = self.vmax
            else:
                self.prev = typed_text

            self.save_func(self.prev)
        elif typed_text == "":
            self.set(self.vmin)
            self.prev = self.vmin
            self.save_func(self.prev)
        else:
            self.set(self.prev)

    def toggle_disable(self, disable: bool):
        if disable:
            self.prev_state = str(self.cget('state'))
            self.configure(state='disabled')
        else:
            self.configure(state=self.prev_state)


class CategorizedComboBox(ttk.Combobox):
    """
    A combobox that allow to displays a dropdown menu with categories and items
    """
    def __init__(self, root: Union[Tk, Toplevel], master, categories, callback, *args, **kwargs):
        super().__init__(master, *args, **kwargs)

        self.root = root
        self.categories = categories
        self.callback = callback
        self.configure(state="readonly")
        self.menu = Menu(root, tearoff=0)
        self.is_posted = False

        for category in categories:
            category_menu = Menu(self.menu, tearoff=0)
            if len(categories[category]) == 0:
                self.menu.add_command(label=category, command=lambda c=category: self.set_item(c))
            else:
                self.menu.add_cascade(label=category, menu=category_menu)
                for item in categories[category]:
                    category_menu.add_command(label=item, command=lambda i=item: self.set_item(i))

        self.bind("<Button-1>", self.show_menu)
        self.menu.bind("<FocusOut>", self.unpost_menu)
        self.root.bind("<Button-1>", self.unpost_menu)

    def show_menu(self, event):
        """
        Show the dropdown menu if the combobox is clicked
        Position it based on the combobox location and height
        """
        # check state first, if disabled then do nothing
        if str(self.cget('state')) == 'disabled':
            return

        self.is_posted = True
        self.menu.post(self.winfo_rootx(), self.winfo_rooty() + self.winfo_height())
        self.configure(state="disabled")

    def set_item(self, item):
        """
        Set the combobox value to the item selected in the menu
        """
        self.set(item)
        self.callback(item)
        self.unpost_menu()

    def unpost_menu(self, event=None):
        if not self.is_posted:
            return

        self.is_posted = False
        self.configure(state="readonly")
        self.menu.unpost()
