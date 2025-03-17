import tkinter as tk
from tkinter import messagebox

import ttkbootstrap as ttk
from PIL import Image, ImageTk

from MVP.refactored.frontend.windows.help_window import HelpWindow
from constants import *


class Titlebar(ttk.Frame):
    def __init__(self, main_diagram, custom_canvas):
        super().__init__(main_diagram)
        self.main_diagram = main_diagram
        self.custom_canvas = custom_canvas
        self.config(bootstyle=ttk.LIGHT)

        # File button
        self.file_button = tk.Menubutton(self, text="File",
                                         width=5, indicatoron=False)
        self.file_menu = ttk.Menu(self.file_button, tearoff=False)
        self.file_button.config(menu=self.file_menu)

        # File -> Save as
        self.save_submenu = tk.Menu(self.file_menu, tearoff=False)
        self.save_submenu.add_command(label="png file", command=lambda: self.custom_canvas.save_as_png())
        self.save_submenu.add_command(label="project", command=lambda: self.main_diagram.save_to_file())
        self.save_submenu.add_command(label="hypergraph", command=lambda: self.custom_canvas.export_hypergraph())

        # File -> Generate
        self.generate_submenu = tk.Menu(self.file_menu, tearoff=False)
        self.generate_submenu.add_command(label="TikZ", command=lambda: self.custom_canvas.open_tikz_generator())
        self.generate_submenu.add_command(label="code", command=lambda: self.main_diagram.generate_code())

        # File menu buttons
        self.file_menu.add_cascade(menu=self.save_submenu, label="Save as")
        self.file_menu.add_cascade(menu=self.generate_submenu, label="Generate")
        self.file_menu.add_command(label="New", command=self.handle_new_graph)
        self.file_menu.add_command(label="Import new diagram", command=lambda: self.handle_new_graph(empty=False))
        self.file_menu.add_command(label="Import as sub-diagram", command=self.import_sub_diagram)
        self.file_button.pack(side=ttk.LEFT)

        # Edit button
        self.edit_button = tk.Menubutton(self, text="Edit", width=5, indicatoron=False)
        self.edit_menu = tk.Menu(self.edit_button, tearoff=False)
        self.edit_button.config(menu=self.edit_menu)

        # Edit menu buttons
        self.edit_menu.add_command(label="Search in Project",
                                   command=lambda: self.main_diagram.open_search_window())
        self.edit_button.pack(side=ttk.LEFT)

        # View button
        self.view_button = tk.Menubutton(self, text="View",
                                         width=5, indicatoron=False)
        self.view_menu = tk.Menu(self.view_button, tearoff=False)
        self.view_button.config(menu=self.view_menu)

        # View menu buttons
        self.view_menu.add_command(label="Visualize hypergraph",
                                   command=lambda: self.main_diagram.visualize_as_graph(self.custom_canvas))

        self.view_button.pack(side=ttk.LEFT)

        self.help_logo = (Image.open(ASSETS_DIR + "/help-circle-outline.png"))
        self.help_logo = self.help_logo.resize((21, 21))
        self.help_logo = ImageTk.PhotoImage(self.help_logo)

        help_button = ttk.Label(self, image=self.help_logo, bootstyle="inverse-light")
        help_button.pack(side=ttk.RIGHT, anchor=tk.CENTER, padx=(0, 5))

        help_button.bind("<Button-1>", lambda event: self.open_help_window())

    def open_help_window(self):
        HelpWindow(self.main_diagram)

    def import_sub_diagram(self):
        box = self.custom_canvas.add_box(loc=(200, 100))
        sub_diagram = box.edit_sub_diagram(switch=False)

        main_canvas = self.main_diagram.importer.canvas
        self.main_diagram.importer.canvas = sub_diagram
        is_importing = self.main_diagram.importer.import_diagram()
        for _ in range(len(sub_diagram.inputs)):
            box.add_left_connection()
        for _ in range(len(sub_diagram.outputs)):
            box.add_right_connection()
        self.main_diagram.importer.canvas = main_canvas
        if not is_importing:
            box.delete_box()

    def set_custom_canvas(self, custom_canvas):
        self.custom_canvas = custom_canvas

    def ask_deletion_confirmation(self):
        dialog = messagebox.askyesnocancel(title="Warning",
                                           message="All unsaved progress will be deleted. Do you wish to save?")
        if dialog == tk.NO:
            return tk.NO
        elif dialog == tk.YES:
            self.main_diagram.save_to_file()
            return tk.YES
        else:
            return tk.NONE

    def handle_new_graph(self, empty=True):
        root_canvas = list(self.main_diagram.canvasses.items())[0][1]
        if root_canvas.boxes or root_canvas.spiders or root_canvas.wires or root_canvas.outputs or root_canvas.inputs:
            dialog_result = self.ask_deletion_confirmation()
            if dialog_result == tk.NONE:
                return
            self.main_diagram.switch_canvas(root_canvas)
            root_canvas.delete_everything()
        if not empty:
            self.main_diagram.load_from_file()


