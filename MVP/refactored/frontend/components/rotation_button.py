import tkinter as tk

from PIL import Image
from PIL.ImageTk import PhotoImage

import constants as const


class RotationButton(tk.LabelFrame):
    """
    A LabelFrame wrapper that is used as an indicator for showing the direction/rotation of the diagram.

    Clicking on it will change the direction/rotation of the diagram.
    """

    def __init__(self, master, custom_canvas, **kwargs):
        """
        RotationButton constructor.

        :param master: tk.Tk master widget.
        :param custom_canvas: CustomCanvas that the button controls.
        :param kwargs: key word arguments.
        """
        super().__init__(master, **kwargs)
        self.custom_canvas = custom_canvas

        self.config(height=60, width=60, text="Direction")

        self.arrow_base = Image.open(const.ASSETS_DIR + "/arrow-right-thin.png").resize((60, 50))
        self.arrow = self.arrow_base
        self.arrow_image = PhotoImage(self.arrow_base)

        self.bind("<Button-1>", lambda event: self.rotate_diagram())

        self.button = None
        self.update()

    def update(self):
        """
        Update the RotationButton.

        :return: None
        """
        self.update_location()
        self.update_arrow()

    def update_location(self):
        """
        Update location of the RotationButton.

        Replaces it back to the bottom right corner of the CustomCanvas.

        :return:
        """
        self.place_forget()
        gap_size = 5
        self.place(x=self.custom_canvas.winfo_width() - self.winfo_width() - gap_size,
                   y=self.custom_canvas.winfo_height() - self.winfo_height() - gap_size)

    def update_arrow(self):
        """
        Update the arrow of the button.

        :return: None
        """
        self.arrow = self.arrow_base
        self.arrow = PhotoImage(self.arrow.rotate(-self.custom_canvas.rotation))

        if self.button:
            self.button.pack_forget()
        self.button = tk.Label(self, image=self.arrow)
        self.button.image = self.arrow_image
        self.button.bind("<Button-1>", lambda event: self.rotate_diagram())
        self.button.pack(anchor=tk.CENTER, fill=tk.BOTH, expand=True)

    def rotate_diagram(self):
        """
        Rotate diagram function.

        Activated on button press.

        :return: None
        """
        self.custom_canvas.set_rotation(self.custom_canvas.rotation + 90)
        self.update_arrow()
