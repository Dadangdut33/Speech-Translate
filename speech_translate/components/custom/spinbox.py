from tkinter import ttk, Tk, Toplevel
from typing import Union


def number_only(P):
    return P.isdigit()


def number_only_float(P):
    try:
        float(P)
    except ValueError:
        return False
    return True


def num_check(el, min, max, cb_func=None, converts_to_float=False):
    value = el.get()

    converts_to = float if converts_to_float else int
    if converts_to(value) > max:
        el.set(max)

    if converts_to(value) < min:
        el.set(min)

    if cb_func is not None:
        cb_func()


def max_number(root, el, min, max, cb_func=None):
    # verify value only after user has finished typing
    root.after(1000, lambda: num_check(el, min, max, cb_func))


def max_number_float(root, el, min, max, cb_func=None):
    # verify value only after user has finished typing
    root.after(1000, lambda: num_check(el, min, max, cb_func, True))


class SpinboxNumOnly(ttk.Spinbox):
    """
    Spinbox with limited values
    """
    def __init__(
        self,
        root: Union[Tk, Toplevel],
        master,
        v_min: Union[float, int],
        v_max: Union[float, int],
        callback,
        num_float=False,
        *args,
        **kwargs
    ):
        super().__init__(
            master,
            from_=v_min,
            to=v_max,
            validate="key",
            validatecommand=(root.register(number_only), "%P"),
            *args,
            **kwargs
        )

        self.root = root
        self.v_min = v_min
        self.v_max = v_max
        self.callback = callback

        self.prev = None
        self.verify_after = None

        if num_float:
            self.configure(increment=0.1, format="%.2f", validatecommand=(root.register(number_only_float), "%P"))

        # Bind the KeyRelease event to capture text input
        maxFunc = max_number_float if num_float else max_number
        self.bind(
            "<KeyRelease>",
            lambda e: maxFunc(
                self.root,
                self,
                self.v_min,
                self.v_max,
                lambda *args: self.callback(self.get()),
            ),
        )
