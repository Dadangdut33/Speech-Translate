from tkinter import Text


class ColoredText(Text):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)

    def insert_with_color(self, text: str, color: str):
        # Create a temporary tag with the specified color
        self.tag_configure(color, foreground=color)

        # Insert the text with the color tag
        self.insert("end", text, color)

    def clear_text_and_tags(self):
        self.delete("1.0", "end")
        # clear all tags
        for tag in self.tag_names():
            self.tag_delete(tag)
