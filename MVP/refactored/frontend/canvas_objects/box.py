import json
import math
import os
import re
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog

import constants as const
from MVP.refactored.backend.id_generator import IdGenerator
from MVP.refactored.backend.types.ActionType import ActionType
from MVP.refactored.backend.types.connection_side import ConnectionSide
from MVP.refactored.frontend.canvas_objects.connection import Connection
from MVP.refactored.frontend.canvas_objects.types.connection_type import ConnectionType
from MVP.refactored.frontend.windows.code_editor import CodeEditor


class Box:
    """
    A box is a rectangle on the CustomCanvas. A box can have Connections on it's left and right side.

    Boxes represent a function, the function itself can be defined by the user.

    Boxes are also used to contain sub-diagrams. The sub-diagram is accessible from the treeview on canvases on the left
    side of the application.

    Boxes can contain code. The functions are findable in the "Manage methods" window. Applying code to boxes can be
    done by renaming them to match an existing function or by adding code to them yourself through the code editor.
    Code can only be added to a box with an existing label.

    The coordinates of a Box are the top left corner for it.
    """

    default_size = (60, 60)
    max_label_size = 50

    def __init__(self, canvas, x, y, size=default_size, id_=None, style=const.RECTANGLE):
        """
        Box constructor.

        :param canvas: CustomCanvas object that Box will be created on.
        :param x: X coordinate of the Box.
        :param y: Y coordinate of the Box.
        :param size: (Optional) Tuple with width and height of box.
        :param id_: (Optional) ID of the box.
        :param style: (Optional) Shape of the box.
        """
        self.style = style
        self.canvas = canvas

        x, y = self.canvas.canvasx(x), self.canvas.canvasy(y)
        self.size = self.get_logical_size(size)

        self.x = None
        self.y = None
        self.display_x = None
        self.display_y = None
        self.rel_y = None
        self.rel_x = None
        self.update_coords(x, y)

        self.start_x = self.display_x
        self.start_y = self.display_y

        self.x_dif = 0
        self.y_dif = 0
        self.connections: list[Connection] = []
        self.left_connections = 0
        self.right_connections = 0
        self.label = None
        self.label_text = ""
        self.wires = []
        if not id_:
            self.id = IdGenerator.id()
        else:
            self.id = id_
        self.context_menu = None

        self.extra_shapes = {}
        self.shape = None
        self.resize_handle = None
        self.update_box()

        self.locked = False
        self.sub_diagram = None
        self.receiver = canvas.main_diagram.receiver
        if self.receiver.listener and not self.canvas.is_search:
            self.receiver.receiver_callback(ActionType.BOX_CREATE, generator_id=self.id, canvas_id=self.canvas.id)
            if self.canvas.diagram_source_box:
                self.receiver.receiver_callback(ActionType.BOX_SUB_BOX, generator_id=self.id,
                                                connection_id=self.canvas.diagram_source_box.id,
                                                canvas_id=self.canvas.id)

        self.is_snapped = False

        self.collision_ids = [self.shape, self.resize_handle]

        self.bind_events()

    def remove_wire(self, wire):
        """
        Remove specific wire from Box.

        :param wire: Wire to remove
        :return: None
        """
        self.wires.remove(wire)

    def set_id(self, id_):
        """
        Set Box ID.

        :param id_: New ID of the box.
        :return: None
        """
        if self.receiver.listener and not self.canvas.is_search:
            self.receiver.receiver_callback(ActionType.BOX_SWAP_ID, generator_id=self.id, new_id=id_,
                                            canvas_id=self.canvas.id)
            if self.canvas.diagram_source_box:
                self.receiver.receiver_callback(ActionType.BOX_SUB_BOX, generator_id=self.id,
                                                connection_id=self.canvas.diagram_source_box.id,
                                                canvas_id=self.canvas.id)
        self.id = id_

    def bind_events(self):
        """
        Bind events to Box rectangle and resize handle.

        :return: None
        """
        self.canvas.tag_bind(self.shape, '<Control-ButtonPress-1>', lambda event: self.on_control_press())
        self.canvas.tag_bind(self.shape, '<ButtonPress-1>', self.on_press)
        self.canvas.tag_bind(self.shape, '<B1-Motion>', self.on_drag)
        self.canvas.tag_bind(self.shape, '<ButtonPress-3>', self.show_context_menu)
        self.canvas.tag_bind(self.resize_handle, '<ButtonPress-1>', self.on_resize_press)
        self.canvas.tag_bind(self.resize_handle, '<B1-Motion>', self.on_resize_drag)
        self.canvas.tag_bind(self.resize_handle, '<Enter>', lambda _: self.canvas.on_hover(self))
        self.canvas.tag_bind(self.resize_handle, '<Leave>', lambda _: self.canvas.on_leave_hover())
        self.canvas.tag_bind(self.shape, '<Double-Button-1>', lambda _: self.handle_double_click())
        self.canvas.tag_bind(self.shape, '<Enter>', lambda _: self.canvas.on_hover(self))
        self.canvas.tag_bind(self.shape, '<Leave>', lambda _: self.canvas.on_leave_hover())

    def show_context_menu(self, event):
        """
        Create and display Box context menu.

        :param event: tkinter.Event object that holds location where menu is created.
        :return: None
        """
        self.close_menu()
        self.context_menu = tk.Menu(self.canvas, tearoff=0)

        if not self.sub_diagram:
            self.context_menu.add_command(label="Add code", command=self.open_editor)
            if not self.label_text.strip():
                self.context_menu.entryconfig("Add code", state="disabled", label="Label needed to add code")

        if not self.locked and not self.sub_diagram:
            self.context_menu.add_command(label="Add Left Connection", command=self.add_left_connection)
            self.context_menu.add_command(label="Add Right Connection", command=self.add_right_connection)

            for circle in self.connections:
                self.context_menu.add_command(label=f"Remove {circle.side} connection nr {circle.index}",
                                              command=lambda bound_arg=circle: self.remove_connection(bound_arg))

            sub_menu = tk.Menu(self.context_menu, tearoff=0)
            self.context_menu.add_cascade(menu=sub_menu, label="Shape")

            for shape in const.SHAPES:
                sub_menu.add_command(label=shape, command=lambda style=shape: self.change_shape(style))

        if self.locked:
            self.context_menu.add_command(label="Unlock Box", command=self.unlock_box)
        if not self.locked:
            self.context_menu.add_command(label="Edit label", command=self.edit_label)
            self.context_menu.add_command(label="Edit Sub-Diagram", command=self.edit_sub_diagram)
            self.context_menu.add_command(label="Unfold sub-diagram", command=self.unfold)
            self.context_menu.add_command(label="Lock Box", command=self.lock_box)
        self.context_menu.add_command(label="Save Box to Menu", command=self.save_box_to_menu)
        self.context_menu.add_command(label="Delete Box", command=self.delete_box)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Cancel")
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def unfold(self):
        """
        Unfold sub-diagram contained in Box.

        If a Box is a sub-diagram then this is used for bringing the sub-diagram to its parent canvas.

        :return: None
        """
        if not self.sub_diagram:
            return
        event = tk.Event()
        event.x = self.display_x + self.size[0] / 2
        event.y = self.display_y + self.size[1] / 2
        self.sub_diagram.select_all()
        self.canvas.selector.copy_selected_items(canvas=self.sub_diagram)
        self.on_press(event)
        self.canvas.paste_copied_items(event)

    def open_editor(self):
        """
        Open a CodeEditor for Box.

        :return: None
        """
        CodeEditor(self.canvas.main_diagram, box=self)

    def save_box_to_menu(self):
        """
        Save Box to config file.

        Saves the Box and it's attributes to a config file, which allows the Box to be imported from menus.

        :return: None
        """
        if not self.label_text:
            self.edit_label()
        if not self.label_text:
            return
        self.canvas.main_diagram.save_box_to_diagram_menu(self)

    def handle_double_click(self):
        """
        Handle double click action on Box.

        Allows user to select input and output amounts unless the Box has a sub-diagram, in which case the user will
        be moved to the sub-diagram canvas.

        :return: None
        """
        if self.sub_diagram:
            self.canvas.main_diagram.switch_canvas(self.sub_diagram)
        else:
            self.set_inputs_outputs()

    def set_inputs_outputs(self):
        """
        Set input and output amounts for Box.

        Opens 2 dialogs requiring the user to input the wanted amounts of inputs and outputs.
        The entered amounts will be applied to the Box.

        :return: None
        """
        if self.locked:
            return
        # ask for input amount
        inputs = simpledialog.askstring(title="Inputs (left connections)", prompt="Enter amount")
        if inputs and not inputs.isdigit():
            while True:
                inputs = simpledialog.askstring(title="Inputs (left connections)",
                                                prompt="Enter amount, must be integer!")
                if inputs:
                    if inputs.isdigit():
                        break
                else:
                    break

        # ask for output amount
        outputs = simpledialog.askstring(title="Outputs (right connections)", prompt="Enter amount")
        if outputs and not outputs.isdigit():
            while True:
                outputs = simpledialog.askstring(title="Outputs (right connections)",
                                                 prompt="Enter amount, must be integer!")
                if outputs:
                    if outputs.isdigit():
                        break
                else:
                    break

        # select connections to remove
        to_be_removed = []
        for c in self.connections:
            if c.side == const.RIGHT and outputs:
                to_be_removed.append(c)
            if c.side == const.LEFT and inputs:
                to_be_removed.append(c)

        # remove selected connectionsS
        for c in to_be_removed:
            c.delete()
            self.remove_connection(c)
            self.update_connections()
            self.update_wires()

        # add new connections
        if not self.canvas.is_search:
            self.receiver.receiver_callback(ActionType.BOX_REMOVE_ALL_CONNECTIONS, generator_id=self.id,
                                            canvas_id=self.canvas.id)
        if outputs:
            for _ in range(int(outputs)):
                self.add_right_connection()
        if inputs:
            for _ in range(int(inputs)):
                self.add_left_connection()

    def edit_sub_diagram(self, save_to_canvasses=True, switch=True):
        """
        Edit the Box sub-diagram.

        Will create a sub-diagram in the Box. If a sub-diagram already exists it will open it. Returns sub-diagram
        CustomCanvas object.

        :param save_to_canvasses: boolean to save canvas
        :param switch: boolean for switching canvas to sub-diagram after creation.
        :return: CustomCanvas sub-diagram
        """
        from MVP.refactored.frontend.components.custom_canvas import CustomCanvas
        if not self.sub_diagram:
            self.sub_diagram = CustomCanvas(self.canvas.main_diagram, self.canvas.main_diagram,
                                            id_=self.id, highlightthickness=0,
                                            diagram_source_box=self, rotation=self.canvas.rotation)
            self.canvas.itemconfig(self.shape, fill="#dfecf2")
            if save_to_canvasses:
                name = self.label_text
                if not name:
                    name = str(self.sub_diagram.id)[-6:]
                    self.set_label(name)
                self.sub_diagram.set_name(name)
                self.canvas.main_diagram.add_canvas(self.sub_diagram)
                self.canvas.main_diagram.update_canvas_name(self.sub_diagram)
                if switch:
                    self.canvas.main_diagram.switch_canvas(self.sub_diagram)

        else:
            if switch:
                self.canvas.main_diagram.switch_canvas(self.sub_diagram)

        if self.receiver.listener and not self.canvas.is_search:
            self.receiver.receiver_callback(ActionType.BOX_COMPOUND, generator_id=self.id, canvas_id=self.canvas.id,
                                            new_canvas_id=self.sub_diagram.id)
        return self.sub_diagram

    def close_menu(self):
        """
        Close the Box context menu.

        :return: None
        """
        if self.context_menu:
            self.context_menu.destroy()

    # MOVING, CLICKING ETC.
    def on_press(self, event):
        """
        Handle press action for Box.

        Sets variables to allow dragging of the Box. Clears previous selection and selects the Box.

        :param event: tkinter.Event object holding the location of the action.
        :return: None
        """
        event.x, event.y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        for item in self.canvas.selector.selected_items:
            item.deselect()
        self.canvas.selector.selected_boxes.clear()
        self.canvas.selector.selected_spiders.clear()
        self.canvas.selector.selected_wires.clear()
        self.canvas.selector.selected_items.clear()
        self.select()
        self.canvas.selector.selected_items.append(self)
        self.start_x = event.x
        self.start_y = event.y
        self.x_dif = event.x - self.display_x
        self.y_dif = event.y - self.display_y

    def on_control_press(self):
        """
        Handle control press action for Box.

        This method will select or unselect the Box depending on previous select state. It will not clear the previously
        selected items.

        :return: None
        """
        if self in self.canvas.selector.selected_items:
            self.canvas.selector.selected_items.remove(self)
            self.deselect()
        else:
            self.select()
            self.canvas.selector.selected_items.append(self)
        self.canvas.selector.select_wires_between_selected_items()

    def on_drag(self, event, from_configuration=False):
        """
        Handle dragging action for Box.

        :param event: tkinter.Event for dragging locations.
        :param from_configuration: (Optional) Boolean stating if the call to drag is coming due to canvas configuration.
        :return: None
        """
        if event.state & 0x4:
            return
        event.x, event.y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

        event.x, event.y = self.update_coords_by_size(event.x, event.y)

        self.start_x = event.x
        self.start_y = event.y

        go_to_x = event.x - self.x_dif
        go_to_y = event.y - self.y_dif

        # snapping into place
        found = False
        size = self.get_logical_size(self.size)
        go_to_x, go_to_y = self.canvas.convert_coords(go_to_x, go_to_y, to_logical=True)
        if not from_configuration:
            for box in self.canvas.boxes:
                if box == self:
                    continue
                box_size = box.get_logical_size(box.size)
                if abs(box.x + box_size[0] / 2 - (go_to_x + size[0] / 2)) < box_size[0] / 2 + size[0] / 2:
                    go_to_x = box.x + box_size[0] / 2 - size[0] / 2

                    found = True
            for spider in self.canvas.spiders:
                if abs(spider.location[0] - (go_to_x + size[0] / 2)) < size[0] / 2 + spider.r:
                    go_to_x = spider.x - size[0] / 2

                    found = True
            if found:
                collision = self.find_collisions(go_to_x, go_to_y)

                if len(collision) != 0:
                    if self.is_snapped:
                        return

                    jump_size = 10
                    counter = 0
                    while collision:
                        if counter % 2 == 0:
                            go_to_y += counter * jump_size
                        else:
                            go_to_y -= counter * jump_size

                        collision = self.find_collisions(go_to_x, go_to_y)

                        counter += 1

        self.is_snapped = found

        go_to_x, go_to_y = self.canvas.convert_coords(go_to_x, go_to_y, to_display=True)
        self.move(go_to_x, go_to_y, bypass_legality=from_configuration)
        self.move_label()

    def update_self_collision_ids(self):
        """
        Update collision ids that are attached to the Box.

        Will update collision_ids with new label tag or Connections tags.

        :return: None
        """
        self.collision_ids = [self.shape, self.resize_handle]
        if self.label:
            self.collision_ids.append(self.label)
        for connection in self.connections:
            self.collision_ids.append(connection.circle)
        for extra_tag in self.extra_shapes.values():
            self.collision_ids.append(extra_tag)

    def find_collisions(self, go_to_x, go_to_y):
        """
        Return list of tags that would be colliding with the Box if it was at go_to_x and go_to_y coordinates.

        :param go_to_x: X coordinate where the Box would be.
        :param go_to_y: Y coordinate where the Box would be.
        :return: List of tags that would be colliding with the Box in the given location.
        """
        self.update_self_collision_ids()
        go_to_x, go_to_y = self.canvas.convert_coords(go_to_x, go_to_y, to_display=True)

        if self.canvas.rotation == 90 or self.canvas.rotation == 180:
            collision = self.canvas.find_overlapping(go_to_x - self.size[0], go_to_y, go_to_x, go_to_y + self.size[1])
        elif self.canvas.rotation == 270:
            collision = self.canvas.find_overlapping(go_to_x, go_to_y, go_to_x - self.size[0], go_to_y - self.size[1])
        else:
            collision = self.canvas.find_overlapping(go_to_x, go_to_y, go_to_x + self.size[0], go_to_y + self.size[1])

        collision = list(collision)
        for index in self.collision_ids:
            if index in collision:
                collision.remove(index)
        for wire_label in self.canvas.wire_label_tags:
            if wire_label in collision:
                collision.remove(wire_label)
        for wire in self.canvas.wires:
            tag = wire.line
            if tag in collision:
                collision.remove(tag)
        return collision

    def on_resize_scroll(self, event):
        """
        Resize the Box based on event.

        Handles the ctrl + scroll event on Box. Will resize it accordingly to delta attribute of tkinter.Event.

        :param event: tkinter.Event object.
        :return: None
        """
        if event.delta == 120:
            multiplier = 1
        else:
            multiplier = -1
        if multiplier == -1:
            if 20 > min(self.size):
                return
        old_size = self.size
        new_size_x, new_size_y = self.get_logical_size((self.size[0] + 5 * multiplier, self.size[1] + 5 * multiplier))
        self.size = (new_size_x, new_size_y)
        match self.canvas.rotation:
            case 90:
                self.size = (new_size_y, new_size_x)
                if self.find_collisions(self.x, self.y - (new_size_x - old_size[1])):
                    self.size = old_size
                    return
            case 180:
                if self.find_collisions(self.x - (new_size_x - old_size[0]), self.y):
                    self.size = old_size
                    return
            case 270:
                if self.find_collisions(self.x - (new_size_y - old_size[0]), self.y - (new_size_x - old_size[1])):
                    self.size = old_size
                    return
            case _:
                if self.find_collisions(self.x, self.y):
                    self.size = old_size
                    return
        self.size = old_size
        self.update_size(new_size_x, new_size_y)
        self.move_label()

    def on_resize_drag(self, event):
        """
        Resize the Box based on mouse movement.

        Handles dragging on the resize handle.

        :param event: tkinter.Event object.
        :return: None
        """
        event.x, event.y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        resize_x = self.display_x + self.size[0] - 10
        resize_y = self.display_y + self.size[1] - 10
        dx = event.x - self.start_x
        dy = event.y - self.start_y

        if dx > 0 and not resize_x <= event.x:
            dx = 0

        if dy > 0 and not resize_y <= event.y:
            dy = 0

        self.start_x = event.x
        self.start_y = event.y
        new_size_x = max(20, self.size[0] + dx)
        new_size_y = max(20, self.size[1] + dy)
        new_size_x, new_size_y = self.get_logical_size((new_size_x, new_size_y))
        self.update_size(new_size_x, new_size_y)
        self.move_label()

    def resize_by_connections(self):
        """
        Resize the Box based on the amount of Connections.

        Resizes the Box so all Connections could have an appropriate amount of space between them.

        :return: None
        """
        nr_cs = max([c.index for c in self.connections] + [0])
        height = max([50 * nr_cs, 50])
        if self.canvas.is_vertical():
            if self.size[0] < height:
                self.update_size(self.size[1], height)
                self.move_label()
        else:
            if self.size[1] < height:
                self.update_size(self.size[0], height)
                self.move_label()

    def move_label(self):
        """
        Move label to the center of the Box.

        :return: None
        """
        if self.label:
            self.canvas.coords(self.label, self.display_x + self.size[0] / 2, self.display_y + self.size[1] / 2)

    def bind_event_label(self):
        """
        Bind events to the Box label.

        :return: None
        """
        self.canvas.tag_bind(self.label, '<B1-Motion>', self.on_drag)
        self.canvas.tag_bind(self.label, '<ButtonPress-3>', self.show_context_menu)
        self.canvas.tag_bind(self.label, '<Double-Button-1>', lambda _: self.handle_double_click())
        self.canvas.tag_bind(self.label, '<Control-ButtonPress-1>', lambda event: self.on_control_press())
        self.canvas.tag_bind(self.label, '<ButtonPress-1>', self.on_press)
        self.canvas.tag_bind(self.label, '<Enter>', lambda _: self.canvas.on_hover(self))
        self.canvas.tag_bind(self.label, '<Leave>', lambda _: self.canvas.on_leave_hover())

    def edit_label(self, new_label=None):
        """
        Edit Box label.

        If no parameters are given, the user will be asked to enter a label for the Box.
        With parameters asking the user for input is skipped and the new label will be applied to the box immediately.

        :param new_label: (Optional) New label for the box.
        :return: None
        """
        if new_label is None:
            text = simpledialog.askstring("Input", "Enter label:", initialvalue=self.label_text)
            if text is not None:
                if len(text) > Box.max_label_size:
                    self.canvas.main_diagram.show_error_dialog(f"Label must be less than {Box.max_label_size}"
                                                               f" characters.")
                    return self.edit_label()
                self.label_text = text
            if os.stat(const.FUNCTIONS_CONF).st_size != 0:
                with open(const.FUNCTIONS_CONF, "r") as file:
                    data = json.load(file)
                    for label, code in data.items():
                        if label == self.label_text:
                            if messagebox.askokcancel("Confirmation",
                                                      "A box with this label already exists."
                                                      " Do you want to use the existing box?"):
                                self.update_io()
                            else:
                                return self.edit_label()
        else:
            if len(new_label) > Box.max_label_size:
                return
            self.label_text = new_label

        self.update_label()

        if self.label_text:
            self.receiver.receiver_callback(action=ActionType.BOX_ADD_LABEL, new_label=self.label_text,
                                            generator_id=self.id, canvas_id=self.canvas.id)

            if self.sub_diagram:
                self.sub_diagram.set_name(self.label_text)
                self.canvas.main_diagram.update_canvas_name(self.sub_diagram)

        self.bind_event_label()

    def update_label(self):
        """
        Create or update label.

        This will create or update a label based on the label_text variable

        :return: None
        """
        if self.receiver.listener and not self.canvas.is_search:
            self.receiver.receiver_callback(ActionType.BOX_ADD_OPERATOR, generator_id=self.id, operator=self.label_text,
                                            canvas_id=self.canvas.id)
        if not self.label:
            self.label = self.canvas.create_text((self.display_x + self.size[0] / 2, self.display_y + self.size[1] / 2),
                                                 text=self.label_text, fill=const.BLACK, font=('Helvetica', 14))
            self.collision_ids.append(self.label)
        else:
            self.canvas.itemconfig(self.label, text=self.label_text)
        label_width = abs(self.canvas.bbox(self.label)[0] - self.canvas.bbox(self.label)[2])
        if label_width > self.size[0]:
            self.size = [label_width + 20, self.size[1]]
        self.update_size(*self.get_logical_size(self.size))
        self.move_label()

    def set_label(self, new_label):
        """
        Set label for Box.

        :param new_label: New label text.
        :return: None
        """
        self.label_text = new_label
        self.update_label()
        self.bind_event_label()

    def on_resize_press(self, event):
        """
        Handles pressing on the resize handle.

        Sets variables start_(x/y) to allow for dragging.

        :param event: tkinter.Event object.
        :return: None
        """
        self.start_x = event.x
        self.start_y = event.y

    def move(self, new_x, new_y, bypass_legality=False):
        """
        Move the Box to a new location.

        Will move the Box to a new location unless the move is not legal.

        :param new_x: X coordinate Box will be moved to.
        :param new_y: Y coordinate Box will be moved to.
        :param bypass_legality: If movement should bypass legality checks.
        :return:
        """
        new_x = round(new_x, 4)
        new_y = round(new_y, 4)
        new_x, new_y = self.canvas.convert_coords(new_x, new_y, to_logical=True)
        is_bad = False
        for connection in self.connections:
            if connection.has_wire and self.is_illegal_move(connection, new_x, bypass=bypass_legality):
                is_bad = True
                break
        if is_bad:
            self.update_coords(self.x, new_y)

        else:
            self.update_coords(new_x, new_y)
        self.update_box()
        self.update_connections()
        self.update_wires()
        self.rel_x = round(self.display_x / self.canvas.winfo_width(), 4)
        self.rel_y = round(self.display_y / self.canvas.winfo_height(), 4)

    def select(self):
        """
        Apply the select style to the Box.

        Turns the Box outline and Connections into green.

        :return: None
        """
        self.canvas.itemconfig(self.shape, outline=const.SELECT_COLOR)
        [c.select() for c in self.connections]

    def search_highlight_secondary(self):
        """
        Apply the secondary search highlight style.

        Applies the secondary search highlight style to the Box. Changes outline color and Connections colors. Will
        add the Box to CustomCanvas list containing search highlighted objects.

        :return: None
        """
        self.canvas.itemconfig(self.shape, outline=const.SECONDARY_SEARCH_COLOR)
        [c.search_highlight_secondary() for c in self.connections]
        self.canvas.search_result_highlights.append(self)

    def search_highlight_primary(self):
        """
        Apply primary search highlight style.

        Applies the primary search highlight style to the Box. Changes outline color and Connections colors. Will
        add the Box to CustomCanvas list containing search highlighted objects.

        :return: None
        """
        self.canvas.itemconfig(self.shape, outline=const.PRIMARY_SEARCH_COLOR)
        [c.search_highlight_primary() for c in self.connections]
        self.canvas.search_result_highlights.append(self)

    def deselect(self):
        """
        Deselect the Box.

        Turns the outline of the Box to black along with its Connections.

        :return: None
        """
        self.canvas.itemconfig(self.shape, outline=const.BLACK)
        [c.deselect() for c in self.connections]

    def lock_box(self):
        """
        Lock the Box.

        Turns locked value to True.

        :return: None
        """
        self.locked = True

    def unlock_box(self):
        """
        Unlock the Box.

        Turns the locked value to False.

        :return: None
        """
        self.locked = False

    # UPDATES
    def update_size(self, new_size_x, new_size_y):
        """
        Update Box size.

        Update the Size and locations of items attached to the Box.

        :param new_size_x: New logical width
        :param new_size_y: New logical height
        :return: None
        """
        if self.canvas.is_vertical():  # keeps display_y in the same spot
            self.y = self.y - (new_size_y - self.get_logical_size(self.size)[1])
        if self.canvas.rotation == 180 or self.canvas.rotation == 270:  # keeps display_x in the same spot
            self.x = self.x - (new_size_x - self.get_logical_size(self.size)[0])

        self.size = self.get_logical_size((new_size_x, new_size_y))
        self.update_coords(self.x, self.y)
        self.update_box()
        self.update_connections()
        self.update_wires()

    def update_connections(self):
        """
        Update Connection locations of Box.

        :return: None
        """
        for c in self.connections:
            conn_x, conn_y = self.get_connection_coordinates(c.side, c.index)
            c.update_location((conn_x, conn_y))

    def update_wires(self):
        """
        Update Wires.

        Updates Wires that are connected to the Box.

        :return: None
        """
        [wire.update() for wire in self.wires]

    def update_io(self):
        """
        Update inputs and outputs of Box.

        Updates the inputs and outputs of a Box based on the code that is added to it.

        :return: None
        """
        with open(const.FUNCTIONS_CONF, "r") as file:
            data = json.load(file)
            for label, code in data.items():
                if label == self.label_text:
                    inputs_amount, outputs_amount = self.get_input_output_amount_off_code(code)
                    if inputs_amount > self.left_connections:
                        for i in range(inputs_amount - self.left_connections):
                            self.add_left_connection()
                    elif inputs_amount < self.left_connections:
                        for j in range(self.left_connections - inputs_amount):
                            for con in self.connections[::-1]:
                                if con.side == const.LEFT:
                                    self.remove_connection(con)
                                    break

                    if outputs_amount > self.right_connections:
                        for i in range(outputs_amount - self.right_connections):
                            self.add_right_connection()
                    elif outputs_amount < self.right_connections:
                        for i in range(self.right_connections - outputs_amount):
                            for con in self.connections[::-1]:
                                if con.side == const.RIGHT:
                                    self.remove_connection(con)
                                    break

    # ADD TO/REMOVE FROM CANVAS
    def add_wire(self, wire):
        """
        Add a wire to the Box.

        :param wire: Wire to be added.
        :return: None
        """
        if wire not in self.wires:
            self.wires.append(wire)

    def add_left_connection(self, id_=None, connection_type=ConnectionType.GENERIC):
        """
        Add a Connection to the left side of the Box.

        Creates and adds a Connection to the left side of the Box.

        :param id_: (Optional) ID that will be added to the Connection.
        :param connection_type: (Optional) Type of Connection that will be added.
        :return: Connection object
        """
        i = self.get_new_left_index()
        conn_x, conn_y = self.get_connection_coordinates(const.LEFT, i)
        connection = Connection(self, i, const.LEFT, (conn_x, conn_y), self.canvas, id_=id_,
                                connection_type=connection_type)
        self.left_connections += 1
        self.connections.append(connection)
        self.collision_ids.append(connection.circle)

        self.update_connections()
        self.update_wires()
        if self.receiver.listener and not self.canvas.is_search:
            self.receiver.receiver_callback(ActionType.BOX_ADD_LEFT, generator_id=self.id, connection_nr=i,
                                            connection_id=connection.id, canvas_id=self.canvas.id)

        self.resize_by_connections()
        return connection

    def add_right_connection(self, id_=None, connection_type=ConnectionType.GENERIC):
        """
        Add a Connection to the right side of the Box.

        Creates and adds a Connection to the right side of the Box.

        :param id_: (Optional) ID that will be added to the Connection.
        :param connection_type: (Optional) Type of Connection that will be added.
        :return: Connection object
        """
        i = self.get_new_right_index()
        conn_x, conn_y = self.get_connection_coordinates(const.RIGHT, i)
        connection = Connection(self, i, const.RIGHT, (conn_x, conn_y), self.canvas, id_=id_,
                                connection_type=connection_type)
        self.right_connections += 1
        self.connections.append(connection)
        self.collision_ids.append(connection.circle)

        self.update_connections()
        self.update_wires()
        if self.receiver.listener and not self.canvas.is_search:
            self.receiver.receiver_callback(ActionType.BOX_ADD_RIGHT, generator_id=self.id, connection_nr=i,
                                            connection_id=connection.id, canvas_id=self.canvas.id)
        self.resize_by_connections()
        return connection

    def remove_connection(self, connection):
        """
        Remove a Connection from the box.

        Removes the given Connection from the Box.

        :param connection: Connection that will be removed
        :return: None
        """
        for c in self.connections:
            if c.index > connection.index and connection.side == c.side:
                c.lessen_index_by_one()
        if self.receiver.listener and not self.canvas.is_search:
            if connection.side == ConnectionSide.LEFT:
                self.receiver.receiver_callback(ActionType.BOX_REMOVE_LEFT, generator_id=self.id,
                                                connection_nr=connection.index, connection_id=connection.id,
                                                canvas_id=self.canvas.id)
            elif connection.side == ConnectionSide.RIGHT:
                self.receiver.receiver_callback(ActionType.BOX_REMOVE_RIGHT, generator_id=self.id,
                                                connection_nr=connection.index, connection_id=connection.id,
                                                canvas_id=self.canvas.id)
        if connection.side == const.LEFT:
            self.left_connections -= 1
        elif connection.side == const.RIGHT:
            self.right_connections -= 1

        self.connections.remove(connection)
        self.collision_ids.remove(connection.circle)
        connection.delete()
        self.update_connections()
        self.update_wires()
        self.resize_by_connections()

    def delete_box(self, keep_sub_diagram=False):
        """
        Delete Box.

        Delete the Box, its Connections and sub-diagram if chosen to.

        :param keep_sub_diagram: (Optional) Specify whether the sub-diagram will be kept.
        :return: None
        """
        for c in self.connections:
            c.delete()

        self.canvas.delete(self.shape)
        self.canvas.delete(self.resize_handle)

        if self in self.canvas.boxes:
            self.canvas.boxes.remove(self)
        self.canvas.delete(self.label)
        for tag in self.extra_shapes.values():
            self.canvas.delete(tag)
        if self.sub_diagram and not keep_sub_diagram:
            self.canvas.main_diagram.del_from_canvasses(self.sub_diagram)
        if self.receiver.listener and not self.canvas.is_search:
            self.receiver.receiver_callback(ActionType.BOX_DELETE, generator_id=self.id, canvas_id=self.canvas.id)

    # BOOLEANS
    def is_illegal_move(self, connection, new_x, bypass=False):
        """
        Check whether move to new_x is illegal.

        Will take a Connection and an x coordinate and check whether moving the connection to the x coordinate is legal.

        :param connection: Connection that the new location
        :param new_x: x coordinate to move to.
        :param bypass: if legality checking will be bypassed.
        :return: boolean if move is illegal
        """
        if bypass:
            return False
        wire = connection.wire
        if connection.side == const.LEFT:
            if connection == wire.start_connection:
                other_connection = wire.end_connection
            else:
                other_connection = wire.start_connection
            other_x = other_connection.location[0]
            if other_x + other_connection.width_between_boxes >= new_x:
                return True

        if connection.side == const.RIGHT:
            if connection == wire.start_connection:
                other_connection = wire.end_connection
            else:
                other_connection = wire.start_connection

            other_x = other_connection.location[0]
            if other_x - other_connection.width_between_boxes <= new_x + self.get_logical_size(self.size)[0]:
                return True
        return False

    # HELPERS
    def get_connection_coordinates(self, side, index):
        """
        Return coordinates for a Connection.

        Returns coordinates for a Connection at one side of the Box at index.

        :param side: Side of Box that the Connection would be on.
        :param index: Index at which the Connection would be on the given side.
        :return: Tuple of coordinates for a Connection.
        """
        if side == const.LEFT:
            i = self.get_new_left_index()
            return self.x, self.y + (index + 1) * self.get_logical_size(self.size)[1] / (i + 1)

        elif side == const.RIGHT:
            i = self.get_new_right_index()
            return (self.x + self.get_logical_size(self.size)[0],
                    self.y + (index + 1) * self.get_logical_size(self.size)[1] / (i + 1))

    def get_new_left_index(self):
        """
        Return a new index for the left side of the Box.

        :return: int
        """
        if not self.left_connections > 0:
            return 0
        return max([c.index if c.side == const.LEFT else 0 for c in self.connections]) + 1

    def get_new_right_index(self):
        """
        Return a new index for the right side of the Box.

        :return: int
        """
        if not self.right_connections > 0:
            return 0
        return max([c.index if c.side == const.RIGHT else 0 for c in self.connections]) + 1

    def change_shape(self, shape):
        """
        Change shape of Box.

        Works by creating a new copied Box with a different shape.

        :param shape: Shape of new Box
        :return: None
        """
        match shape:
            case const.RECTANGLE:
                new_box = self.canvas.add_box((self.x, self.y), self.get_logical_size(self.size), style=const.RECTANGLE)
            case const.TRIANGLE:
                new_box = self.canvas.add_box((self.x, self.y), self.get_logical_size(self.size), style=const.TRIANGLE)
            case const.AND_GATE:
                new_box = self.canvas.add_box((self.x, self.y), self.get_logical_size(self.size), style=const.AND_GATE)
            case const.OR_GATE:
                new_box = self.canvas.add_box((self.x, self.y), self.get_logical_size(self.size), style=const.OR_GATE)
            case const.XOR_GATE:
                new_box = self.canvas.add_box((self.x, self.y), self.get_logical_size(self.size), style=const.XOR_GATE)
            case _:
                return
        self.canvas.copier.copy_box(self, new_box)
        self.delete_box()

    @staticmethod
    def get_input_output_amount_off_code(code):
        """
        Return amount of inputs and outputs based off code.

        Returns the amount of inputs and outputs in code.

        :param code: String code
        :return: Tuple of input and output amount
        """
        inputs = re.search(r"\((.*)\)", code).group(1)
        outputs = re.search(r"return (.*)\n*", code)
        if outputs:
            outputs = outputs.group(1)
        else:
            outputs = ""

        inputs_amount = len(inputs.split(","))
        outputs_amount = len(outputs.strip().split(","))
        if not inputs:
            inputs_amount = 0
        if not outputs:
            outputs_amount = 0
        return inputs_amount, outputs_amount

    def update_box(self):
        """
        Update the Box display.

        Redirects to shape updating functions that will create or update the location of the Box on the canvas.

        :return: None
        """
        match self.style:
            case const.RECTANGLE:
                self.__update_rectangle__()
            case const.TRIANGLE:
                self.__update_triangle__()
            case const.AND_GATE:
                self.__update_and_gate__()
            case const.OR_GATE:
                self.__update_or_gate__()
            case const.XOR_GATE:
                self.__update_xor_gate__()
            case _:
                self.__update_rectangle__()
        self.__update_resize_handle__()

    def __update_rectangle__(self):
        """
        Update/create rectangle shape Box.

        :return: None
        """
        w, h = self.get_logical_size(self.size)
        points = [
            (0, 0),
            (w, 0),
            (w, h),
            (0, h)
                  ]
        rotated = self.rotate_point(points)
        if self.shape:
            self.canvas.coords(self.shape, *rotated)
        else:
            self.shape = self.canvas.create_polygon(*rotated, outline=const.BLACK, fill=const.WHITE)

    def __update_triangle__(self):
        """
        Update/create triangle shape Box.

        :return: None
        """
        w, h = self.get_logical_size(self.size)
        points = [
            (w, h / 2),
            (0, 0),
            (0, h),
        ]
        rotated = self.rotate_point(points)
        if self.shape:
            self.canvas.coords(self.shape, *rotated)
        else:
            self.shape = self.canvas.create_polygon(*rotated, outline=const.BLACK, fill=const.WHITE)

    def __update_and_gate__(self):
        """
        Update/create AND gate shape Box.

        :return: None
        """
        w, h = self.get_logical_size(self.size)
        points = [
            (0, 0),
            (0, 0),
            (w / 2, 0),
            (w / 2, 0),
            (0.75 * w, h / 20),
            (0.85 * w, h / 8),
            (0.95 * w, h / 4),
            (1 * w, h / 2),
            (0.95 * w, 3 * h / 4),
            (0.85 * w, 7 * h / 8),
            (0.75 * w, 19 * h / 20),
            (w / 2, h),
            (w / 2, h),
            (0, h),
            (0, h)
        ]
        rotated = self.rotate_point(points)
        if self.shape:
            self.canvas.coords(self.shape, *rotated)
        else:
            self.shape = self.canvas.create_polygon(*rotated, smooth=1, splinesteps=20,
                                                    outline=const.BLACK, fill=const.WHITE)

    def __update_or_gate__(self):
        """
        Update/create OR gate shape Box.

        :return: None
        """
        w, h = self.get_logical_size(self.size)
        points = [
            (0, 0),
            (0, 0),
            (w / 3, 0),
            (w / 3, 0),
            (0.8 * w, h / 7),
            (0.99 * w, h / 2 - 1),
            (1 * w, h / 2),
            (1 * w, h / 2),
            (0.99 * w, h / 2 + 1),
            (0.8 * w, 6 * h / 7),
            (w / 3, h),
            (w / 3, h),
            (0, h),
            (0, h),
            (w / 8, 4 * h / 5),
            (w / 4, h / 2),
            (w / 8, h / 5)
        ]
        rotated = self.rotate_point(points)
        if self.shape:
            self.canvas.coords(self.shape, *rotated)
        else:
            self.shape = self.canvas.create_polygon(*rotated, smooth=1, splinesteps=20,
                                                    outline=const.BLACK, fill=const.WHITE)

    def __update_xor_gate__(self):
        """
        Update/create XOR gate shape Box.

        :return: None
        """
        w, h = self.get_logical_size(self.size)
        points = [
            (self.x - 5, self.y),
            (self.x - 5, self.y),
            (self.x + w / 8 - 5, self.y + h / 5),
            (self.x + w / 4 - 5, self.y + h / 2),
            (self.x + w / 8 - 5, self.y + 4 * h / 5),
            (self.x - 5, self.y + h),
            (self.x - 5, self.y + h),
            (self.x + w / 8 - 5, self.y + 4 * h / 5),
            (self.x + w / 4 - 5, self.y + h / 2),
            (self.x + w / 8 - 5, self.y + h / 5)
        ]
        rotated = [self.canvas.convert_coords(x, y) for x, y in points]
        if self.shape:
            if "xor line" in self.extra_shapes:
                self.canvas.coords(self.extra_shapes["xor line"], *rotated)
        else:
            self.extra_shapes["xor line"] = self.canvas.create_polygon(*rotated,
                                                                       smooth=1, spline=20,
                                                                       fill=const.WHITE, outline=const.BLACK)
        self.__update_or_gate__()

    def __update_resize_handle__(self):
        """
        Update/create resize handle for Box.

        Creates a black square known as the resize handle at the bottom left of the Box.

        :return: None
        """
        w, h = self.size
        if self.resize_handle:
            self.canvas.coords(self.resize_handle, self.display_x + w - 10, self.display_y + h - 10,
                               self.display_x + w, self.display_y + h)
        else:
            self.resize_handle = self.canvas.create_rectangle(self.display_x + self.size[0] - 10,
                                                              self.display_y + self.size[1] - 10,
                                                              self.display_x + self.size[0],
                                                              self.display_y + self.size[1],
                                                              outline=const.BLACK, fill=const.BLACK)

    def update_coords(self, x, y):
        """
        Updates Box logical and display coordinates based on MainDiagram rotation.

        :param x: The new logical x-coordinate of the Box.
        :param y: The new logical y-coordinate of the Box.
        :return: None
        """
        self.x = x
        self.y = y
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if self.canvas.winfo_width() <= 1:
            width = self.canvas.main_diagram.custom_canvas.winfo_width()
            height = self.canvas.main_diagram.custom_canvas.winfo_height()

        match self.canvas.rotation:
            case 90:
                self.display_x = width - (y + self.size[0])
                self.display_y = x
            case 180:
                self.display_x = width - (x + self.size[0])
                self.display_y = y
            case 270:
                self.display_x = width - (y + self.size[0])
                self.display_y = height - (x + self.size[1])
            case _:
                self.display_x = x
                self.display_y = y
        self.rel_x = round(self.display_x / width, 4)
        self.rel_y = round(self.display_y / height, 4)

    def get_logical_size(self, size):
        """
        Return the logical size of the Box, adjusted for the diagram's rotation.

        :param size: The size of the Box as [width, height].
        :return: The logical size of the Box after rotation adjustment.
        """
        match self.canvas.rotation:
            case 90 | 270:
                return [size[1], size[0]]
            case _:
                return [*size]

    def rotate_point(self, points):
        """
        Rotate box point around its own center based on canvas rotation and translates them to display coordinates.

        :param points: A list of (x, y) tuples representing the original point coordinates.
        :return: A list of coordinates after rotation and translation.
        """
        w, h = self.get_logical_size(self.size)
        rotated = []
        cx = w / 2
        cy = h / 2
        angle = math.radians(self.canvas.rotation)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        for x, y in points:
            dx = x - cx
            dy = y - cy
            rotated.append(
                (cx + dx * cos_a - dy * sin_a, cy + dx * sin_a + dy * cos_a))

        min_x = min(x for x, y in rotated)
        min_y = min(y for x, y in rotated)
        shifted = [(x - min_x, y - min_y) for x, y in rotated]
        translated = [(x + self.display_x, y + self.display_y) for x, y in shifted]
        flat_points = [coord for point in translated for coord in point]

        return flat_points

    def update_coords_by_size(self, x, y):
        """
        Adjust x and y coordinates based on rotation and box size.

        :param x: x coordinate.
        :param y: y coordinate.
        :return: x and y coordinates.
        """
        if self.canvas.rotation == 90 or self.canvas.rotation == 180:
            x = x + self.size[0]
        if self.canvas.rotation == 270:
            x = x + self.size[0]
            y = y + self.size[1]

        return x, y
