import json
import re
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog

from MVP.refactored.frontend.canvas_objects.connection import Connection
from MVP.refactored.frontend.canvas_objects.types.connection_type import ConnectionType
from MVP.refactored.frontend.windows.code_editor import CodeEditor
from constants import *


class Box:
    def __init__(self, canvas, x, y, receiver, size=(60, 60), id_=None, shape="rectangle"):
        self.shape = shape
        self.canvas = canvas
        x, y = self.canvas.canvasx(x), self.canvas.canvasy(y)
        self.x = x
        self.y = y
        self.start_x = x
        self.start_y = y
        self.size = size
        self.x_dif = 0
        self.y_dif = 0
        self.connections: list[Connection] = []
        self.left_connections = 0
        self.right_connections = 0
        self.label = None
        self.label_text = ""
        self.wires = []
        if not id_:
            self.id = id(self)
        else:
            self.id = id_
        self.node = None
        self.context_menu = tk.Menu(self.canvas, tearoff=0)
        self.rect = self.create_rect()

        self.resize_handle = self.canvas.create_rectangle(self.x + self.size[0] - 10, self.y + self.size[1] - 10,
                                                          self.x + self.size[0], self.y + self.size[1],
                                                          outline="black", fill="black")
        self.locked = False
        self.bind_events()
        self.sub_diagram = None
        self.receiver = receiver
        if self.receiver.listener and not self.canvas.search:
            self.receiver.receiver_callback("box_add", generator_id=self.id)
            if self.canvas.diagram_source_box:
                self.receiver.receiver_callback("sub_box", generator_id=self.id,
                                                connection_id=self.canvas.diagram_source_box.id)

        self.is_snapped = False

        self.collision_ids = [self.rect, self.resize_handle]

    def set_id(self, id_):
        if self.receiver.listener and not self.canvas.search:
            self.receiver.receiver_callback("box_swap_id", generator_id=self.id, connection_id=id_)
            if self.canvas.diagram_source_box:
                self.receiver.receiver_callback("sub_box", generator_id=self.id,
                                                connection_id=self.canvas.diagram_source_box.id)
        self.id = id_

    def bind_events(self):
        self.canvas.tag_bind(self.rect, '<Control-ButtonPress-1>', lambda event: self.on_control_press())
        self.canvas.tag_bind(self.rect, '<ButtonPress-1>', self.on_press)
        self.canvas.tag_bind(self.rect, '<B1-Motion>', self.on_drag)
        self.canvas.tag_bind(self.rect, '<ButtonPress-3>', self.show_context_menu)
        self.canvas.tag_bind(self.resize_handle, '<ButtonPress-1>', self.on_resize_press)
        self.canvas.tag_bind(self.resize_handle, '<B1-Motion>', self.on_resize_drag)
        self.canvas.tag_bind(self.resize_handle, '<Enter>', lambda _: self.canvas.on_hover(self))
        self.canvas.tag_bind(self.resize_handle, '<Leave>', lambda _: self.canvas.on_leave_hover())
        self.canvas.tag_bind(self.rect, '<Double-Button-1>', lambda _: self.handle_double_click())
        self.canvas.tag_bind(self.rect, '<Enter>', lambda _: self.canvas.on_hover(self))
        self.canvas.tag_bind(self.rect, '<Leave>', lambda _: self.canvas.on_leave_hover())

    def show_context_menu(self, event):
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
            sub_menu.add_command(label="Rectangle", command=lambda shape="rectangle": self.change_shape(shape))
            sub_menu.add_command(label="Triangle", command=lambda shape="triangle": self.change_shape(shape))

        if self.locked:
            self.context_menu.add_command(label="Unlock Box", command=self.unlock_box)
        if not self.locked:
            self.context_menu.add_command(label="Edit label", command=self.edit_label)
            self.context_menu.add_command(label="Edit Sub-Diagram", command=self.edit_sub_diagram)
            self.context_menu.add_command(label="Unfold sub-diagram", command=self.unfold)
            self.context_menu.add_command(label="Lock Box", command=self.lock_box)
        self.context_menu.add_command(label="Save Box to Menu", command=self.save_box_to_menu)
        if self.sub_diagram:
            self.context_menu.add_command(label="Delete Box", command=lambda: self.delete_box(action="sub_diagram"))
        else:
            self.context_menu.add_command(label="Delete Box", command=self.delete_box)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Cancel")
        self.context_menu.tk_popup(event.x_root, event.y_root)

    def unfold(self):
        if not self.sub_diagram:
            return
        event = tk.Event()
        event.x = self.x + self.size[0] / 2
        event.y = self.y + self.size[1] / 2
        self.sub_diagram.select_all()
        self.canvas.selector.copy_selected_items(canvas=self.sub_diagram)
        self.on_press(event)
        self.canvas.paste_copied_items(event)

    def open_editor(self):
        CodeEditor(self.canvas.main_diagram, box=self)

    def save_box_to_menu(self):
        if not self.label_text:
            self.edit_label()
        if not self.label_text:
            return
        self.canvas.main_diagram.save_box_to_diagram_menu(self)

    def handle_double_click(self):
        if self.sub_diagram:
            self.canvas.main_diagram.switch_canvas(self.sub_diagram)
        else:
            self.set_inputs_outputs()

    def set_inputs_outputs(self):
        if self.locked:
            return
        # ask for inputs amount
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

        # ask for outputs amount
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
            if c.side == "right" and outputs:
                to_be_removed.append(c)
            if c.side == "left" and inputs:
                to_be_removed.append(c)

        # remove selected connectionsS
        for c in to_be_removed:
            c.delete()
            self.remove_connection(c)
            self.update_connections()
            self.update_wires()

        # add new connections
        if not self.canvas.search:
            self.receiver.receiver_callback("box_remove_connection_all", generator_id=self.id)
        if outputs:
            for _ in range(int(outputs)):
                self.add_right_connection()
        if inputs:
            for _ in range(int(inputs)):
                self.add_left_connection()

    def edit_sub_diagram(self, save_to_canvasses=True, add_boxes=True, switch=True):
        from MVP.refactored.frontend.components.custom_canvas import CustomCanvas
        if self.receiver.listener and not self.canvas.search:
            self.receiver.receiver_callback("compound", generator_id=self.id)
        if not self.sub_diagram:
            self.sub_diagram = CustomCanvas(self.canvas.main_diagram, self, self.receiver, self.canvas.main_diagram,
                                            self.canvas, add_boxes, self.id, highlightthickness=0)
            self.canvas.itemconfig(self.rect, fill="#dfecf2")
            if save_to_canvasses:
                name = self.label_text
                if not name:
                    name = str(self.sub_diagram.id)[-6:]
                    self.set_label(name)
                self.sub_diagram.set_name(name)
                self.canvas.main_diagram.add_canvas(self.sub_diagram)
                self.canvas.main_diagram.change_canvas_name(self.sub_diagram)
                if switch:
                    self.canvas.main_diagram.switch_canvas(self.sub_diagram)

            return self.sub_diagram
        else:
            if switch:
                self.canvas.main_diagram.switch_canvas(self.sub_diagram)
            return self.sub_diagram

    def close_menu(self):
        if self.context_menu:
            self.context_menu.destroy()

    # MOVING, CLICKING ETC.
    def on_press(self, event):
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
        self.x_dif = event.x - self.x
        self.y_dif = event.y - self.y

    def on_control_press(self):
        if self in self.canvas.selector.selected_items:
            self.canvas.selector.selected_items.remove(self)
            self.deselect()
        else:
            self.select()
            self.canvas.selector.selected_items.append(self)
        self.canvas.selector.select_wires_between_selected_items()

    def on_drag(self, event):
        if event.state & 0x4:
            return
        event.x, event.y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

        self.start_x = event.x
        self.start_y = event.y

        go_to_x = event.x - self.x_dif
        go_to_y = event.y - self.y_dif

        # snapping into place
        found = False
        for box in self.canvas.boxes:
            if box == self:
                continue

            if abs(box.x + box.size[0] / 2 - (go_to_x + self.size[0] / 2)) < box.size[0] / 2 + self.size[0] / 2:
                go_to_x = box.x + box.size[0] / 2 - +self.size[0] / 2

                found = True
        for spider in self.canvas.spiders:

            if abs(spider.location[0] - (go_to_x + self.size[0] / 2)) < self.size[0] / 2 + spider.r:
                go_to_x = spider.x - +self.size[0] / 2

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

        self.move(go_to_x, go_to_y)
        self.move_label()

    def get_self_collision_ids(self):
        self.collision_ids = [self.rect, self.resize_handle]
        if self.label:
            self.collision_ids.append(self.label)
        for connection in self.connections:
            self.collision_ids.append(connection.circle)

    def find_collisions(self, go_to_x, go_to_y):
        self.get_self_collision_ids()
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
        if event.delta == 120:
            multiplier = 1
        else:
            multiplier = -1
        if multiplier == -1:
            if 20 > min(self.size):
                return
        old_size = self.size
        self.size = (self.size[0] + 5 * multiplier, self.size[1] + 5 * multiplier)
        if self.find_collisions(self.x, self.y):
            self.size = old_size
            return
        self.update_size(self.size[0] + 5 * multiplier, self.size[1] + 5 * multiplier)
        self.move_label()

    def on_resize_drag(self, event):
        event.x, event.y = self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)
        resize_x = self.x + self.size[0] - 10
        resize_y = self.y + self.size[1] - 10
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
        self.update_size(new_size_x, new_size_y)
        self.move_label()

    def resize_by_connections(self):
        # TODO resize by label too if needed
        nr_cs = max([c.index for c in self.connections] + [0])
        height = max([50 * nr_cs, 50])
        if self.size[1] < height:
            self.update_size(self.size[0], height)
            self.move_label()

    def move_label(self):
        if self.label:
            self.canvas.coords(self.label, self.x + self.size[0] / 2, self.y + self.size[1] / 2)

    def bind_event_label(self):
        self.canvas.tag_bind(self.label, '<B1-Motion>', self.on_drag)
        self.canvas.tag_bind(self.label, '<ButtonPress-3>', self.show_context_menu)
        self.canvas.tag_bind(self.label, '<Double-Button-1>', lambda _: self.handle_double_click())
        self.canvas.tag_bind(self.label, '<Control-ButtonPress-1>', lambda event: self.on_control_press())
        self.canvas.tag_bind(self.label, '<ButtonPress-1>', self.on_press)
        self.canvas.tag_bind(self.label, '<Enter>', lambda _: self.canvas.on_hover(self))
        self.canvas.tag_bind(self.label, '<Leave>', lambda _: self.canvas.on_leave_hover())

    def edit_label(self, new_label=None):
        if new_label is None:
            text = simpledialog.askstring("Input", "Enter label:", initialvalue=self.label_text)
            if text is not None:
                self.label_text = text
            if os.stat(FUNCTIONS_CONF).st_size != 0:
                with open(FUNCTIONS_CONF, "r") as file:
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
            self.label_text = new_label

        self.change_label()

        if self.label_text:
            if self.sub_diagram:
                self.sub_diagram.set_name(self.label_text)
                self.canvas.main_diagram.change_canvas_name(self.sub_diagram)

        self.bind_event_label()

    def change_label(self):
        if self.receiver.listener and not self.canvas.search:
            self.receiver.receiver_callback("box_add_operator", generator_id=self.id, operator=self.label_text)
        if not self.label:
            self.label = self.canvas.create_text((self.x + self.size[0] / 2, self.y + self.size[1] / 2),
                                                 text=self.label_text, fill="black", font=('Helvetica', 14))
            self.collision_ids.append(self.label)
        else:
            self.canvas.itemconfig(self.label, text=self.label_text)

    def set_label(self, new_label):
        self.label_text = new_label
        self.change_label()
        self.bind_event_label()

    def on_resize_press(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def move(self, new_x, new_y):
        new_x = round(new_x, 4)
        new_y = round(new_y, 4)
        is_bad = False
        for connection in self.connections:
            if connection.has_wire and self.is_illegal_move(connection, new_x):
                is_bad = True
                break
        if is_bad:
            self.y = new_y
            self.update_position()
            self.update_connections()
            self.update_wires()
        else:
            self.x = new_x
            self.y = new_y
            self.update_position()
            self.update_connections()
            self.update_wires()

    def select(self):
        self.canvas.itemconfig(self.rect, outline="green")
        [c.select() for c in self.connections]

    def search_highlight_secondary(self):
        self.canvas.itemconfig(self.rect, outline="orange")
        [c.search_highlight_secondary() for c in self.connections]
        self.canvas.search_result_highlights.append(self)

    def search_highlight_primary(self):
        self.canvas.itemconfig(self.rect, outline="cyan")
        [c.search_highlight_primary() for c in self.connections]
        self.canvas.search_result_highlights.append(self)

    def deselect(self):
        self.canvas.itemconfig(self.rect, outline="black")
        [c.deselect() for c in self.connections]

    def lock_box(self):
        self.locked = True

    def unlock_box(self):
        self.locked = False

    # UPDATES
    def update_size(self, new_size_x, new_size_y):
        self.size = (new_size_x, new_size_y)
        self.update_position()
        self.update_connections()
        self.update_wires()

    def update_position(self):
        if self.shape == "rectangle":
            self.canvas.coords(self.rect, self.x, self.y, self.x + self.size[0], self.y + self.size[1])
        if self.shape == "triangle":
            self.canvas.coords(self.rect,
                               self.x + self.size[0], self.y + self.size[1] / 2,
                               self.x, self.y,
                               self.x, self.y + self.size[1])
        self.canvas.coords(self.resize_handle, self.x + self.size[0] - 10, self.y + self.size[1] - 10,
                           self.x + self.size[0], self.y + self.size[1])

    def update_connections(self):
        for c in self.connections:
            conn_x, conn_y = self.get_connection_coordinates(c.side, c.index)
            c.move_to((conn_x, conn_y))

    def update_wires(self):
        [wire.update() for wire in self.wires]

    def update_io(self):
        """Update inputs and outputs based on label and code."""
        with open(FUNCTIONS_CONF, "r") as file:
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
                                if con.side == "left":
                                    self.remove_connection(con)
                                    break

                    if outputs_amount > self.right_connections:
                        for i in range(outputs_amount - self.right_connections):
                            self.add_right_connection()
                    elif outputs_amount < self.right_connections:
                        for i in range(self.right_connections - outputs_amount):
                            for con in self.connections[::-1]:
                                if con.side == "right":
                                    self.remove_connection(con)
                                    break

    # ADD TO/REMOVE FROM CANVAS
    def add_wire(self, wire):
        if wire not in self.wires:
            self.wires.append(wire)

    def add_left_connection(self, id_=None, connection_type=ConnectionType.GENERIC):
        i = self.get_new_left_index()
        conn_x, conn_y = self.get_connection_coordinates("left", i)
        connection = Connection(self, i, "left", (conn_x, conn_y), self.canvas, id_=id_,
                                connection_type=connection_type)
        self.left_connections += 1
        self.connections.append(connection)
        self.collision_ids.append(connection.circle)

        self.update_connections()
        self.update_wires()
        if self.receiver.listener and not self.canvas.search:
            self.receiver.receiver_callback("box_add_left", generator_id=self.id, connection_nr=i,
                                            connection_id=connection.id)

        self.resize_by_connections()
        return connection

    def add_right_connection(self, id_=None, connection_type=ConnectionType.GENERIC):
        i = self.get_new_right_index()
        conn_x, conn_y = self.get_connection_coordinates("right", i)
        connection = Connection(self, i, "right", (conn_x, conn_y), self.canvas, id_=id_,
                                connection_type=connection_type)
        self.right_connections += 1
        self.connections.append(connection)
        self.collision_ids.append(connection.circle)

        self.update_connections()
        self.update_wires()
        if self.receiver.listener and not self.canvas.search:
            self.receiver.receiver_callback("box_add_right", generator_id=self.id, connection_nr=i,
                                            connection_id=connection.id)
        self.resize_by_connections()
        return connection

    def remove_connection(self, circle):
        for c in self.connections:
            if c.index > circle.index and circle.side == c.side:
                c.lessen_index_by_one()
        if self.receiver.listener and not self.canvas.search:
            self.receiver.receiver_callback("box_remove_connection", generator_id=self.id, connection_nr=circle.index,
                                            generator_side=circle.side)
        if circle.side == "left":
            self.left_connections -= 1
        elif circle.side == "right":
            self.right_connections -= 1

        self.connections.remove(circle)
        self.collision_ids.remove(circle.circle)
        circle.delete()
        self.update_connections()
        self.update_wires()
        self.resize_by_connections()

    def delete_box(self, keep_sub_diagram=False, action=None):
        for c in self.connections:
            c.delete()

        self.canvas.delete(self.rect)
        self.canvas.delete(self.resize_handle)

        if self in self.canvas.boxes:
            self.canvas.boxes.remove(self)
        self.canvas.delete(self.label)
        if self.sub_diagram and not keep_sub_diagram:
            self.canvas.main_diagram.del_from_canvasses(self.sub_diagram)
        if self.receiver.listener and not self.canvas.search:
            if action != "sub_diagram":
                self.receiver.receiver_callback("box_delete", generator_id=self.id)

    # BOOLEANS
    def is_illegal_move(self, connection, new_x):
        wire = connection.wire
        if connection.side == "left":
            if connection == wire.start_connection:
                other_connection = wire.end_connection
            else:
                other_connection = wire.start_connection
            other_x = other_connection.location[0]
            if other_x + other_connection.width_between_boxes >= new_x:
                return True

        if connection.side == "right":
            if connection == wire.start_connection:
                other_connection = wire.end_connection
            else:
                other_connection = wire.start_connection

            other_x = other_connection.location[0]
            if other_x - other_connection.width_between_boxes <= new_x + self.size[0]:
                return True
        return False

    # HELPERS
    def get_connection_coordinates(self, side, index):
        if side == "left":
            i = self.get_new_left_index()
            return self.x, self.y + (index + 1) * self.size[1] / (i + 1)

        elif side == "right":
            i = self.get_new_right_index()
            return self.x + self.size[0], self.y + (index + 1) * self.size[1] / (i + 1)

    def get_new_left_index(self):
        if not self.left_connections > 0:
            return 0
        return max([c.index if c.side == "left" else 0 for c in self.connections]) + 1

    def get_new_right_index(self):
        if not self.right_connections > 0:
            return 0
        return max([c.index if c.side == "right" else 0 for c in self.connections]) + 1

    def create_rect(self):
        w, h = self.size
        if self.shape == "rectangle":
            return self.canvas.create_rectangle(self.x, self.y, self.x + w, self.y + h,
                                                outline="black", fill="white")
        if self.shape == "triangle":
            return self.canvas.create_polygon(self.x + w, self.y + h / 2, self.x, self.y,
                                              self.x, self.y + h, outline="black", fill="white")

    def change_shape(self, shape):
        if shape == "rectangle":
            new_box = self.canvas.add_box((self.x, self.y), self.size, shape="rectangle")
        elif shape == "triangle":
            new_box = self.canvas.add_box((self.x, self.y), self.size, shape="triangle")
        else:
            return
        self.canvas.copier.copy_box(self, new_box)
        self.delete_box()

    @staticmethod
    def get_input_output_amount_off_code(code):
        inputs = re.search(r"\((.*)\)", code).group(1)
        outputs = re.search(r"return (.*)\n*", code).group(1)
        inputs_amount = len(inputs.split(","))
        if outputs[0] == "(":
            outputs = outputs[1:-1]
        outputs_amount = len(outputs.strip().split(","))
        if not inputs:
            inputs_amount = 0
        if not outputs:
            outputs_amount = 0
        return inputs_amount, outputs_amount
