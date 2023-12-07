from tkinter import ttk, Tk, Toplevel
from typing import Union


def number_only(P, allow_empty=False):
    if P == "" and allow_empty:
        return True
    else:
        return P.isdigit()


def number_only_float(P, allow_empty=False):
    if P == "" and allow_empty:
        return True
    else:
        try:
            float(P)
        except ValueError:
            return False
        return True


def num_check(el, min, max, cb_func=None, converts_to_float=False, allow_empty=False):
    value = el.get()
    if value == "" and allow_empty:
        if cb_func is not None:
            cb_func()
        return

    converts_to = float if converts_to_float else int
    if converts_to(value) > max:
        el.set(max)

    if converts_to(value) < min:
        el.set(min)

    if cb_func is not None:
        cb_func()


# verify value only after user has finished typing
def max_number(root, el, min, max, cb_func=None, delay=300, allow_empty=False):
    root.after(delay, lambda: num_check(el, min, max, cb_func, False, allow_empty))


def max_number_float(root, el, min, max, cb_func=None, delay=300, allow_empty=False):
    root.after(delay, lambda: num_check(el, min, max, cb_func, True, allow_empty))


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
        allow_empty=False,
        delay=300,
        initial_value=None,
        *args,
        **kwargs
    ):
        super().__init__(master, from_=v_min, to=v_max, validate="key", *args, **kwargs)
        self.root = root
        self.v_min = v_min
        self.v_max = v_max
        self.callback = callback
        self.prev = None
        self.verify_after = None
        self.allow_empty = allow_empty
        self.delay = delay

        self.increment = kwargs.get("increment", None)

        if initial_value is not None:
            self.set(initial_value)

        if num_float:
            if not self.increment:
                self.increment = 0.1

            self.configure(
                increment=self.increment,
                format="%.2f",
                validatecommand=(root.register(lambda p: number_only_float(p, self.allow_empty)), "%P"),
                command=lambda: self.callback(self.get())
            )
        else:
            if not self.increment:
                self.increment = 1

            self.configure(
                increment=self.increment,
                validatecommand=(root.register(lambda p: number_only(p, self.allow_empty)), "%P"),
                command=lambda: self.callback(self.get())
            )

        # Bind the KeyRelease event to capture text input
        maxFunc = max_number_float if num_float else max_number
        self.bind(
            "<KeyRelease>",
            lambda e: maxFunc(
                self.root, self, self.v_min, self.v_max, lambda *args: self.callback(self.get()), self.delay, self.
                allow_empty
            ),
        )
