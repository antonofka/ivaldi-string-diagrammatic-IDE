import tkinter as tk
from MVP.refactored.frontend.canvas_objects.types.connection_type import ConnectionType


class Connection:

    active_types = 1

    def __init__(self, box, index, side, location, canvas, r=5, id_=None, connection_type=ConnectionType.GENERIC):
        self.canvas = canvas
        self.id = id(self)
        self.box = box  # None if connection is diagram input/output/spider
        self.index = index
        self.side = side  # 'spider' if connection is a spider
        self.location = location
        self.type = connection_type
        self.wire = None
        self.has_wire = False
        self.r = r
        if not id_:
            self.id = id(self)

        else:
            self.id = id_
        self.node = None

        self.context_menu = tk.Menu(self.canvas, tearoff=0)
        self.circle = self.canvas.create_oval(location[0] - self.r, location[1] - self.r, location[0] + self.r,
                                              location[1] + self.r, fill="black",
                                              outline=ConnectionType.COLORS.value[self.type.value],
                                              width=round(min(self.r / 5, 5)))
        self.width_between_boxes = 1  # px
        self.bind_events()

    def update(self):
        self.canvas.itemconfig(self.circle, outline=ConnectionType.COLORS.value[self.type.value])
        self.canvas.itemconfig(self.circle, width=round(min(self.r / 5, 5)))
        self.canvas.update()

    def bind_events(self):
        self.canvas.tag_bind(self.circle, '<ButtonPress-3>', self.show_context_menu)
        self.canvas.tag_bind(self.circle, '<Button-2>', lambda x: self.increment_type())

    def increment_type(self):
        if not self.has_wire:
            self.change_type(self.type.next().value)
            self.increment_active_types()
            self.update()

    def change_type(self, type_id):
        tied_con = self.get_tied_connection()
        if tied_con is None:
            return
        if tied_con and tied_con != self:
            tied_con.type = ConnectionType(type_id)
            tied_con.update()
        if not self.has_wire:
            self.type = ConnectionType(type_id)
            self.update()

    def get_tied_connection(self):
        tied_con = self
        if self.box and self.box.sub_diagram:
            if self.box.sub_diagram == self.canvas:
                connections = self.box.connections
            else:
                connections = self.box.sub_diagram.outputs + self.box.sub_diagram.inputs

            matching_side = ""
            if self.side == "right":
                matching_side = "left"
            elif self.side == "left":
                matching_side = "right"
            for io in connections:
                if io.side == matching_side and io.index == self.index:
                    if io.has_wire:
                        tied_con = None
                    else:
                        tied_con = io
        return tied_con

    def show_context_menu(self, event):
        if not self.wire or not self.wire.is_temporary:
            self.close_menu()
            if (self.box and not self.box.locked) or self.box is None:
                self.context_menu = tk.Menu(self.canvas, tearoff=0)

                self.add_type_choice()

                self.context_menu.add_command(label="Delete Connection", command=self.delete_from_parent)
                self.context_menu.add_separator()
                self.context_menu.add_command(label="Cancel")

                self.context_menu.tk_popup(event.x_root, event.y_root)

    def add_type_choice(self):
        if not self.has_wire:
            sub_menu = tk.Menu(self.context_menu, tearoff=0)
            self.context_menu.add_cascade(menu=sub_menu, label="Connection type")
            sub_menu.add_command(label="Generic", command=lambda: self.change_type(0))

            for i in range(1, Connection.active_types):
                sub_menu.add_command(label=ConnectionType.LABEL_NAMES.value[i],
                                     command=lambda c_type=i: self.change_type(c_type))

            if Connection.active_types < len(ConnectionType.COLORS.value):
                sub_menu.add_separator()
                sub_menu.add_command(label="Add new type", command=lambda: self.add_active_type())

    def add_active_type(self):
        self.change_type(Connection.active_types)
        self.increment_active_types()

    def increment_active_types(self):
        if Connection.active_types < len(ConnectionType.COLORS.value) and self.type.value >= Connection.active_types:
            Connection.active_types += 1

    def close_menu(self):
        if self.context_menu:
            self.context_menu.destroy()

    def delete_from_parent(self):
        if self.box:
            if self.box.sub_diagram and self.side == "left":
                for i in self.box.sub_diagram.inputs:
                    if i.index == self.index:
                        self.box.sub_diagram.remove_specific_diagram_input(i)
                        return
            if self.box.sub_diagram and self.side == "right":
                for i in self.box.sub_diagram.outputs:
                    if i.index == self.index:
                        self.box.sub_diagram.remove_specific_diagram_output(i)
                        return
            self.box.remove_connection(self)
            self.delete()
            return

        if self in self.canvas.inputs:
            self.canvas.remove_specific_diagram_input(self)
            return
        if self in self.canvas.outputs:
            self.canvas.remove_specific_diagram_output(self)
            return

    def change_color(self, color='black'):
        """
        Change the color of the connection. Without a parameter it will turn the Connection to black.

        The function allows usage of all Tkinter built in colors as well as hex code.
         It will change the 'fill' color of the item.

        :param color: string of color name.
        :type color: str
        """
        self.canvas.itemconfig(self.circle, fill=color)

    def move_to(self, location):
        self.canvas.coords(self.circle, location[0] - self.r, location[1] - self.r, location[0] + self.r,
                           location[1] + self.r)
        self.location = location

    def lessen_index_by_one(self):
        self.index -= 1

    def delete(self):
        self.canvas.delete(self.circle)
        if self.has_wire:
            self.canvas.delete(self.wire)
            self.wire.delete_self()

            if self.box and self.wire in self.box.wires:
                self.box.wires.remove(self.wire)

            if self.wire in self.canvas.wires:
                self.canvas.wires.remove(self.wire)

    def add_wire(self, wire):
        if not self.has_wire and self.wire is None:
            self.wire = wire
            self.has_wire = True

    def is_spider(self):
        return False

    def remove_wire(self, wire=None):
        if self.wire:
            self.wire = None
            self.has_wire = False

    def select(self):
        self.canvas.itemconfig(self.circle, fill="green")

    def search_highlight_secondary(self):
        self.canvas.itemconfig(self.circle, fill="orange")
        self.canvas.search_result_highlights.append(self)

    def search_highlight_primary(self):
        self.canvas.itemconfig(self.circle, fill="cyan")
        self.canvas.search_result_highlights.append(self)

    def deselect(self):
        self.canvas.itemconfig(self.circle, fill="black")
