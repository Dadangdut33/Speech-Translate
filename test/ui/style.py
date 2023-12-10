from tkinter import TclError, ttk

if __name__ == "__main__":
    # pylint: disable=consider-using-f-string
    # Debug get stylename options
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

    def iter_layout(layout, tab_amnt=0):
        """Recursively prints the layout children."""
        elements = []
        el_tabs = "  " * tab_amnt
        val_tabs = "  " * (tab_amnt + 1)

        for element, child in layout:
            elements.append(element)
            print(el_tabs + "'{}': {}".format(element, "{"))
            for key, value in child.items():
                if isinstance(value, str):
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
                    for y in layout[n + 2:]:
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
            print(
                '_tkinter.TclError: "{0}" in function'
                "widget_elements_options({0}) is not a regonised stylename.".format(stylename)
            )

    def main():
        style_name_list = list(stylename_map.keys())
        print(">> Stylename List:")
        for stylename in enumerate(style_name_list):
            print("{:<3}{:<20}".format(stylename[0], stylename[1]))

        ask = input("Enter stylename (input nothing to print all): ")

        if len(ask) != 0:
            try:
                name_get = style_name_list[int(ask)]
                stylename_map[name_get]  # check # pylint: disable=pointless-statement

                print("=" * 100)
                stylename_elements_options(name_get)
            except Exception:
                print("Invalid stylename. Input again")
                print("=" * 100)
                main()
        else:
            for stylename in style_name_list:
                print("=" * 100)
                stylename_elements_options(stylename)

    main()
