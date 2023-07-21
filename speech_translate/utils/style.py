"""
Read this first about ttk style:

- Good questions on ttk style
https://stackoverflow.com/questions/48517660/questions-on-using-ttk-style

- ttk style simple example
https://coderslegacy.com/python/tkinter-ttk-style/

- Get ttk style options
https://stackoverflow.com/questions/45389166/how-to-know-all-style-options-of-a-ttk-widget

"""
import os
import tkinter as tk
from speech_translate.custom_logging import logger
from speech_translate.globals import gc, sj
from speech_translate._path import dir_theme
from speech_translate.components.custom.message import mbox
from tkinter import ttk, TclError

theme_list = ["sv-light", "sv-dark"]


def set_ui_style(theme: str, root=None):
    success = False
    try:
        logger.debug("Setting theme: %s", theme)
        set_theme(theme)
        success = True
    except Exception as e:
        logger.exception(e)
        logger.debug("Setting theme failed, converting back to default native theme")
        mbox("Error", f"Failed to set `{theme}` theme, converting back to default native theme", 2, root)
        theme = gc.native_theme
        set_theme(theme)
        sj.savePartialSetting("theme", theme)

    # -----------------------
    assert gc.style is not None
    # Global style
    if "light" in theme.lower() or theme == gc.native_theme:
        logger.debug("Setting custom light theme style")
        gc.style.configure("Bottom.TFrame", background="#f0f0f0")
        gc.style.configure("Brighter.TFrame", background="#ffffff")
        gc.style.configure("BrighterTFrameBg.TLabel", background="#ffffff")
        gc.style.configure("Darker.TFrame", background="#000000")
    else:
        logger.debug("Setting custom dark theme style")
        gc.style.configure("Bottom.TFrame", background="#1e1e1e")
        gc.style.configure("Brighter.TFrame", background="#2e2e2e")
        gc.style.configure("BrighterTFrameBg.TLabel", background="#2e2e2e")
        gc.style.configure("Darker.TFrame", background="#bdbdbd")

    return success


def get_root() -> tk.Tk:
    assert gc.mw is not None
    return gc.mw.root


def init_theme():
    dir_theme_list = [name for name in os.listdir(dir_theme) if os.path.isdir(os.path.join(dir_theme, name))]  # only if a dir

    # filter path list by making sure that the dir name contains .tcl with the same name as the dir
    dir_theme_list = [dir for dir in dir_theme_list if dir + ".tcl" in os.listdir(os.path.join(dir_theme, dir))]

    for dir in dir_theme_list:
        path = os.path.abspath(os.path.join(dir_theme, dir, (dir + ".tcl")))
        theme_list.append(dir)

        try:
            get_root().tk.call("source", str(path))
        except AttributeError as e:
            logger.exception(e)


def get_current_theme() -> str:
    theme = get_root().tk.call("ttk::style", "theme", "use")

    return theme


def get_theme_list():
    return theme_list


def set_theme(theme: str):
    real_theme_list = list(get_root().tk.call("ttk::style", "theme", "names"))
    real_theme_list.extend(theme_list)
    if theme not in real_theme_list:
        raise Exception("not a valid theme name: {}".format(theme))

    try:
        get_root().tk.call("set_theme", theme)
    except TclError as e:
        logger.exception(e)

# -----------------------------
if __name__ == "__main__":
    """
    Debug get stylename options
    """

    stylename_map = {
        "TButton": ttk.Button,
        "TCheckbutton": ttk.Checkbutton,
        "TCombobox": ttk.Combobox,
        "TEntry": ttk.Entry,
        "TFrame": ttk.Frame,
        "TLabel": ttk.Label,
        "TLabelFrame": ttk.LabelFrame,
        "TMenubutton": ttk.Menubutton,
        "TNotebook": ttk.Notebook,
        "TPanedwindow": ttk.Panedwindow,
        "TProgressbar": ttk.Progressbar,
        "Horizontal.TProgressbar": ttk.Progressbar,
        "Vertical.TProgressbar": ttk.Progressbar,
        "TRadiobutton": ttk.Radiobutton,
        "TScale": ttk.Scale,
        "Horizontal.TScale": ttk.Scale,
        "Vertical.TScale": ttk.Scale,
        "TScrollbar": ttk.Scrollbar,
        "Horizontal.TScrollbar": ttk.Scrollbar,
        "Vertical.TScrollbar": ttk.Scrollbar,
        "TSeparator": ttk.Separator,
        "TSizegrip": ttk.Sizegrip,
        "TSpinbox": ttk.Spinbox,
        "Treeview": ttk.Treeview,
    }


    def iter_layout(layout, tab_amnt=0, elements=[]):
        """Recursively prints the layout children."""
        el_tabs = "  " * tab_amnt
        val_tabs = "  " * (tab_amnt + 1)

        for element, child in layout:
            elements.append(element)
            print(el_tabs + "'{}': {}".format(element, "{"))
            for key, value in child.items():
                if type(value) == str:
                    print(val_tabs + "'{}' : '{}',".format(key, value))
                else:
                    print(val_tabs + "'{}' : [(".format(key))
                    iter_layout(value, tab_amnt=tab_amnt + 3)
                    print(val_tabs + ")]")

            print(el_tabs + "{}{}".format("} // ", element))

        return elements


    def stylename_elements_options(stylename):
        """Function to expose the options of every element associated to a widget
        stylename."""
        try:
            # Get widget elements
            style = ttk.Style()
            widget = stylename_map[stylename](None)

            # layouts
            print("Stylename = {}\n".format(stylename))

            config = widget.configure()
            print("{:*^50}".format("Config"))
            for key, value in config.items():
                print("{:<15}{:^10}{}".format(key, "=>", value))

            # layouts
            print("\n{:*^50}".format("Layout"))
            elements = iter_layout(style.layout(stylename))

            layout = str(style.layout(stylename))
            elements = []
            for n, x in enumerate(layout):
                if x == "(":
                    element = ""
                    for y in layout[n + 2 :]:
                        if y != ",":
                            element = element + str(y)
                        else:
                            elements.append(element[:-1])
                            break
            print("\nElement(s) = {}\n".format(elements))

            # Get options of widget elements
            for element in elements:
                print("{0:30} options: {1}".format(element, style.element_options(element)))

        except TclError:
            print('_tkinter.TclError: "{0}" in function' "widget_elements_options({0}) is not a regonised stylename.".format(stylename))

    def main():
        stylenameList = list(stylename_map.keys())
        print(">> Stylename List:")
        for stylename in enumerate(stylenameList):
            print("{:<3}{:<20}".format(stylename[0], stylename[1]))

        ask = input("Enter stylename (input nothing to print all): ")

        if len(ask) != 0:
            try:
                styleNameGet = stylenameList[int(ask)]
                stylename_map[styleNameGet]  # check

                print("=" * 100)
                stylename_elements_options(styleNameGet)
            except Exception:
                print("Invalid stylename. Input again")
                print("=" * 100)
                main()
        else:
            for stylename in stylenameList:
                print("=" * 100)
                stylename_elements_options(stylename)

    main()
