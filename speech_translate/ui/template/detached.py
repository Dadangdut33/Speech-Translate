from platform import system
from tkinter import IntVar, Menu, Tk, Toplevel, ttk
from typing import Literal

from speech_translate._path import p_app_icon
from speech_translate.linker import bc, sj
from speech_translate.ui.custom.label import DraggableHtmlLabel
from speech_translate.ui.custom.message import mbox
from speech_translate.ui.custom.tooltip import tk_tooltip
from speech_translate.utils.audio.beep import beep
from speech_translate.utils.helper import emoji_img


class SubtitleWindow:
    """Detached Subtitle Window"""

    # ----------------------------------------------------------------------
    def __init__(self, master: Tk, title: str, win_type: Literal["tc", "tl"]):
        dark = "dark" in sj.cache["theme"]
        self.close_emoji = emoji_img(16, "❌", dark)
        self.copy_emoji = emoji_img(16, "📋", dark)
        self.pin_emoji = emoji_img(16, "📌", dark)
        self.help_emoji = emoji_img(16, "❓", dark)
        self.title_emoji = emoji_img(16, "🪟", dark)
        self.up_emoji = emoji_img(16, "⬆️", dark)
        self.down_emoji = emoji_img(16, "⬇️", dark)

        self.master = master
        self.title = title
        self.root = Toplevel(master)
        self.root.title(title)
        self.root.geometry(sj.cache.get(f"ex_{win_type}_geometry"))
        self.root.minsize(200, 50)
        self.root.configure(background=sj.cache.get(f"tb_ex_{win_type}_bg_color", ""))
        self.root.wm_withdraw()

        # ------------------ #
        self.win_type = win_type
        self.win_str = ""
        self.x_menu = 0
        self.y_menu = 0
        self.cur_opac: float = 1.0
        self.always_on_top = IntVar()
        self.no_tooltip = IntVar()
        self.no_title_bar = IntVar()
        self.click_through = IntVar()
        if win_type == "tc":
            bc.ex_tcw = self  # type: ignore
            self.win_str = "Transcribe"
        elif win_type == "tl":
            bc.ex_tlw = self  # type: ignore
            self.win_str = "Translate"

        self.lbl_text = DraggableHtmlLabel(self.root, self.root)
        self.lbl_text.configure(background=sj.cache.get(f"tb_ex_{win_type}_bg_color", ""), state="disabled")
        self.lbl_text.pack(side="top", fill="both", expand=True)
        self.f_tooltip = tk_tooltip(
            self.lbl_text,
            "Right click for interaction menu and help ❓\n\nTo resize this window you will need to show the " \
            "title bar first\n\nTo hide this tooltip you can check the Hide Tooltip option in the menu or press Alt + X",
            wrap_len=250,
        )

        self.hidden_sb_y = ttk.Scrollbar(self.lbl_text, orient="vertical")
        # self.hidden_sb_y.pack(side="right", fill="y")
        self.lbl_text.configure(yscrollcommand=self.hidden_sb_y.set)
        self.hidden_sb_y.configure(command=self.lbl_text.yview)

        self.menu_dropdown = Menu(self.root, tearoff=0)
        self.menu_dropdown.add_command(label=self.title, command=self.open_menu, image=self.title_emoji, compound="left")
        self.menu_dropdown.add_command(label="Help", command=self.show_help, image=self.help_emoji, compound="left")
        self.menu_dropdown.add_command(
            label="Copy",
            command=self.copy_tb_content,
            accelerator="Alt + C",
            image=self.copy_emoji,
            compound="left",
        )
        self.menu_dropdown.add_separator()
        self.menu_dropdown.add_checkbutton(
            label="Hide Title bar",
            command=lambda: self.toggle_title_bar(from_keybind=False),
            onvalue=1,
            offvalue=0,
            variable=self.no_title_bar,
            accelerator="Alt + T",
        )
        self.menu_dropdown.add_checkbutton(
            label="Hide Tooltip",
            command=lambda: self.toggle_tooltip(from_keybind=False),
            onvalue=1,
            offvalue=0,
            variable=self.no_tooltip,
            accelerator="Alt + X",
        )
        if system() == "Windows":
            self.click_through.set(sj.cache.get(f"ex_{win_type}_click_through", 0))
            self.menu_dropdown.add_checkbutton(
                label="Click Through/Transparent",
                command=lambda: self.toggle_click_through(from_keybind=False),
                onvalue=1,
                offvalue=0,
                variable=self.click_through,
                accelerator="Alt + S",
            )
            self.toggle_click_through(from_keybind=False, on_init=True)
        self.menu_dropdown.add_checkbutton(
            label="Always On Top",
            command=lambda: self.toggle_always_on_top(from_keybind=False),
            onvalue=1,
            offvalue=0,
            variable=self.always_on_top,
            accelerator="Alt + O",
            image=self.pin_emoji,
            compound="right",
        )
        self.menu_dropdown.add_separator()
        self.menu_dropdown.add_command(
            label="Increase Opacity by 0.1",
            command=self.increase_opacity,
            accelerator="Alt + Mouse Wheel Up",
            image=self.up_emoji,
            compound="left",
        )
        self.menu_dropdown.add_command(
            label="Decrease Opacity by 0.1",
            command=self.decrease_opacity,
            accelerator="Alt + Mouse Wheel Down",
            image=self.down_emoji,
            compound="left",
        )
        self.menu_dropdown.add_separator()
        self.menu_dropdown.add_command(label="Close", command=self.on_closing, image=self.close_emoji, compound="left")

        # ------------------------------------------------------------------------
        # Binds
        # On Close
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # rclick menu
        self.root.bind("<Button-3>", self.open_menu)

        # keybinds
        if system() == "Windows":
            self.root.bind("<Alt-KeyPress-s>", lambda event: self.toggle_click_through())
        self.root.bind("<Alt-KeyPress-c>", lambda event: self.copy_tb_content())
        self.root.bind("<Alt-KeyPress-t>", lambda event: self.toggle_title_bar())
        self.root.bind("<Alt-KeyPress-o>", lambda event: self.toggle_always_on_top())
        self.root.bind("<Alt-KeyPress-x>", lambda event: self.toggle_tooltip())
        self.root.bind("<Alt-MouseWheel>", self.change_opacity)

        # ------------------ Set Icon ------------------
        try:
            self.root.iconbitmap(p_app_icon)
        except Exception:
            pass

        # init settings
        self.__init_settings()

    def __init_settings(self):
        self.always_on_top.set(int(sj.cache[f"ex_{self.win_type}_always_on_top"]))
        self.toggle_always_on_top(from_keybind=False, on_init=True)

        self.no_title_bar.set(int(sj.cache[f"ex_{self.win_type}_no_title_bar"]))
        self.toggle_title_bar(from_keybind=False, on_init=True)

        self.no_tooltip.set(int(sj.cache[f"ex_{self.win_type}_no_tooltip"]))
        self.toggle_tooltip(from_keybind=False, on_init=True)

    def open_menu(self, event=None):
        """
        Method to open the menu.
        """
        if event:
            self.x_menu = event.x_root
            self.y_menu = event.y_root
            self.menu_dropdown.post(event.x_root, event.y_root)
        else:
            self.menu_dropdown.post(self.x_menu, self.y_menu)

    def show_help(self):
        """
        Help window.
        """
        extra = "- Alt + s to toggle click through or transparent window\n" if system() == "Windows" else ""

        mbox(
            f"{self.title} - Help",
            "This is a window that shows the result of the recording session in a separate window. You can think of this as"
            " a subtitle box. To drag the window, drag from the label (text result).\n\n"
            "Keybinds (when focused):\n"
            "- Alt + scroll to change opacity\n"
            "- Alt + c to copy text\n"
            "- Alt + t to toggle title bar (remove title bar)\n"
            f"{extra}"
            "- Alt + o to toggle always on top\n"
            "- Alt + x to toggle on/off tooltip",
            0,
            self.root,
        )

    # toggle tooltip
    def toggle_tooltip(self, from_keybind=True, on_init=False):
        """
        Method to toggle tooltip.
        If from keybind, then toggle the value manually.
        If on init, then don't save the setting and don't beep.
        """
        if from_keybind:
            self.no_tooltip.set(0 if self.no_tooltip.get() == 1 else 1)

        if not on_init:
            beep()
            sj.save_key(f"ex_{self.win_type}_no_tooltip", self.no_tooltip.get())

        if self.no_tooltip.get() == 1:
            self.f_tooltip.hidetip()
            self.f_tooltip.opacity = 0
        else:
            if not on_init:
                self.f_tooltip.show_tip()
            self.f_tooltip.opacity = self.cur_opac

    # show/hide title bar
    def toggle_title_bar(self, from_keybind=True, on_init=False):
        """
        Method to toggle title bar.
        If from keybind, then toggle the value manually.
        If on init, then don't save the setting and don't beep.
        """
        if from_keybind:
            self.no_title_bar.set(0 if self.no_title_bar.get() == 1 else 1)

        if not on_init:
            beep()
            sj.save_key(f"ex_{self.win_type}_no_title_bar", self.no_title_bar.get())

        self.root.overrideredirect(True if self.no_title_bar.get() == 1 else False)

    def update_window_bg(self):
        assert bc.style is not None
        self.root.configure(background=sj.cache[f"tb_ex_{self.win_type}_bg_color"])
        self.lbl_text.configure(background=sj.cache[f"tb_ex_{self.win_type}_bg_color"])

        # check window is transparent or not
        if system() != "Windows":
            return

        if self.click_through.get() == 1:
            self.root.wm_attributes("-transparentcolor", sj.cache[f"tb_ex_{self.win_type}_bg_color"])

    def toggle_click_through(self, from_keybind=True, on_init=False):
        """
        Method to toggle click through. Only on windows.
        If from keybind, then toggle the value manually.
        If on init, then don't save the setting and don't beep.
        """
        if system() != "Windows":
            return
        if from_keybind:
            self.click_through.set(0 if self.click_through.get() == 1 else 1)

        if not on_init:
            beep()
            sj.save_key(f"ex_{self.win_type}_click_through", self.click_through.get())

        if self.click_through.get() == 1:
            self.root.wm_attributes("-transparentcolor", sj.cache[f"tb_ex_{self.win_type}_bg_color"])
        else:
            self.root.wm_attributes("-transparentcolor", "")

    def toggle_always_on_top(self, from_keybind=True, on_init=False):
        """
        Method to toggle always on top.
        If from keybind, then toggle the value manually.
        If on init, then don't save the setting and don't beep.
        """
        if from_keybind:
            self.always_on_top.set(0 if self.always_on_top.get() == 1 else 1)

        if not on_init:
            beep()
            sj.save_key(f"ex_{self.win_type}_always_on_top", self.always_on_top.get())

        self.root.wm_attributes("-topmost", True if self.always_on_top.get() == 1 else False)

    def show(self):
        """
        Method to show the window.
        """
        self.root.wm_deiconify()
        self.root.attributes("-alpha", 1)
        self.show_relative_to_master()
        # disaable click through
        if self.click_through.get() == 1:
            self.click_through.set(0)
            self.root.wm_attributes("-transparentcolor", "")
            sj.save_key(f"ex_{self.win_type}_click_through", self.click_through.get())

    def show_relative_to_master(self):
        x = self.master.winfo_x()
        y = self.master.winfo_y()

        self.root.geometry(f"+{x + 100}+{y + 200}")

    def on_closing(self):
        sj.save_key(f"ex_{self.win_type}_geometry", f"{self.root.winfo_width()}x{self.root.winfo_height()}")
        self.root.wm_withdraw()

    def increase_opacity(self):
        """
        Method to increase the opacity of the window by 0.1.
        """
        self.cur_opac += 0.1
        if self.cur_opac > 1:
            self.cur_opac = 1
        self.root.attributes("-alpha", self.cur_opac)
        self.f_tooltip.opacity = self.cur_opac

    def decrease_opacity(self):
        """
        Method to decrease the opacity of the window by 0.1.
        """
        self.cur_opac -= 0.1
        if self.cur_opac < 0.1:
            self.cur_opac = 0.1
        self.root.attributes("-alpha", self.cur_opac)
        self.f_tooltip.opacity = self.cur_opac

    # opacity change
    def change_opacity(self, event):
        """
        Method to change the opacity of the window by scrolling.

        Args:
            event (event): event object
        """
        if event.delta > 0:
            self.cur_opac += 0.1
        else:
            self.cur_opac -= 0.1

        if self.cur_opac > 1:
            self.cur_opac = 1
        elif self.cur_opac < 0.1:
            self.cur_opac = 0.1
        self.root.attributes("-alpha", self.cur_opac)
        self.f_tooltip.opacity = self.cur_opac

    def copy_tb_content(self):
        """
        Method to copy the textbox content to clipboard.
        """
        self.root.clipboard_clear()
        self.root.clipboard_append(self.lbl_text.get("1.0", "end"))
