import tkinter as tk

from MVP.refactored.frontend.canvas_objects.connection import Connection
from MVP.refactored.frontend.canvas_objects.types.connection_type import ConnectionType


class Spider(Connection):
    def __init__(self, box, index, side, location, canvas, receiver, id_=None, connection_type=ConnectionType.GENERIC):
        self.r = 10
        super().__init__(box, index, side, location, canvas, self.r, connection_type=connection_type)
        self.canvas = canvas
        self.x = location[0]
        self.y = location[1]
        self.location = location
        if not id_:
            self.id = id(self)
        else:
            self.id = id_

        self.connections: list[Connection] = []
        self.context_menu = tk.Menu(self.canvas, tearoff=0)
        self.bind_events()
        self.wires = []
        self.receiver = receiver
        if self.receiver.listener and not self.canvas.search:
            if self.canvas.diagram_source_box:
                self.receiver.receiver_callback('create_spider', wire_id=self.id, connection_id=self.id,
                                                generator_id=self.canvas.diagram_source_box.id)
            else:
                self.receiver.receiver_callback('create_spider', wire_id=self.id, connection_id=self.id)

        self.is_snapped = False

        self.collision_id = self.circle

    def is_spider(self):
        return True

    def bind_events(self):
        self.canvas.tag_bind(self.circle, '<ButtonPress-1>', lambda event: self.on_press())
        self.canvas.tag_bind(self.circle, '<B1-Motion>', self.on_drag)
        self.canvas.tag_bind(self.circle, '<ButtonPress-3>', self.show_context_menu)
        self.canvas.tag_bind(self.circle, '<Control-ButtonPress-1>', lambda event: self.on_control_press())
        self.canvas.tag_bind(self.circle, "<Enter>", lambda _: self.canvas.on_hover(self))
        self.canvas.tag_bind(self.circle, "<Leave>", lambda _: self.canvas.on_leave_hover())
        self.canvas.tag_bind(self.circle, '<Button-2>', lambda x: self.increment_type())

    def show_context_menu(self, event):
        self.close_menu()
        self.context_menu = tk.Menu(self.canvas, tearoff=0)

        self.add_type_choice()

        self.context_menu.add_command(label="Delete Spider", command=self.delete_spider)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Cancel")

        self.context_menu.tk_popup(event.x_root, event.y_root)

    def delete_spider(self, action=None):
        [wire.delete_self(self) for wire in self.wires.copy()]
        self.canvas.spiders.remove(self)
        self.delete()
        if self.receiver.listener and not self.canvas.search:
            if action != "sub_diagram":
                self.receiver.receiver_callback('delete_spider', wire_id=self.id, connection_id=self.id)

    def close_menu(self):
        if self.context_menu:
            self.context_menu.destroy()

    def add_wire(self, wire):
        if wire not in self.wires:
            self.wires.append(wire)
            self.has_wire = True

    def on_resize_scroll(self, event):
        if event.delta == 120:
            multiplier = 1
        else:
            multiplier = -1
        if multiplier == -1:
            if self.r < 5:
                return
        old_r = self.r
        self.r += 2.5 * multiplier
        if self.find_collisions(self.x, self.y):
            self.r = old_r
            return
        self.canvas.coords(self.circle, self.x - self.r, self.y - self.r, self.x + self.r,
                           self.y + self.r)

    # MOVING, CLICKING ETC.
    def on_press(self):
        self.canvas.selector.selected_boxes.clear()
        self.canvas.selector.selected_spiders.clear()
        self.canvas.selector.selected_wires.clear()
        for item in self.canvas.selector.selected_items:
            item.deselect()
        self.canvas.selector.selected_items.clear()
        if not self.canvas.draw_wire_mode:
            if self not in self.canvas.selector.selected_items:
                self.select()
                self.canvas.selector.selected_items.append(self)

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
        if self.canvas.pulling_wire:
            return

        go_to_y = event.y
        go_to_x = self.x
        move_legal = False
        if not self.is_illegal_move(event.x):
            go_to_x = event.x
            move_legal = True

        # snapping into place
        found = False
        for box in self.canvas.boxes:
            if abs(box.x + box.size[0] / 2 - go_to_x) < box.size[0] / 2 + self.r and move_legal:
                go_to_x = box.x + box.size[0] / 2

                found = True
        for spider in self.canvas.spiders:
            if spider == self:
                continue

            cancel = False
            for wire in spider.wires:
                if wire.end_connection == self or wire.start_connection == self:
                    cancel = True
            if cancel:
                continue

            if abs(spider.location[0] - go_to_x) < self.r + spider.r and move_legal:
                go_to_x = spider.location[0]

                found = True
        if found:
            collision = self.find_collisions(go_to_x, go_to_y)
            if len(collision) != 0:
                if self.is_snapped:
                    return

                jump_size = 5
                counter = 0
                while collision:
                    if counter % 2 == 0:
                        go_to_y += counter * jump_size
                    else:
                        go_to_y -= counter * jump_size
                    collision = self.find_collisions(go_to_x, go_to_y)

                    counter += 1

        self.switch_wire_start_and_end()

        self.is_snapped = found

        self.location = [go_to_x, go_to_y]
        self.x = go_to_x
        self.y = go_to_y

        self.canvas.coords(self.circle, self.x - self.r, self.y - self.r, self.x + self.r,
                           self.y + self.r)
        [w.update() for w in self.wires]

    def switch_wire_start_and_end(self):
        for connection in list(filter(lambda x: (x is not None and x != self and x.is_spider()),
                                      [w.end_connection for w in self.wires] + [w.start_connection for w in
                                                                                self.wires])):
            switch = False
            wire = list(filter(lambda w: (w.end_connection == self or w.start_connection == self),
                               connection.wires))[0]
            if wire.start_connection == self and wire.end_connection.x < self.x:
                switch = True
            if wire.end_connection == self and wire.start_connection.x > self.x:
                switch = True
            if switch:
                start = wire.end_connection
                end = wire.start_connection
                wire.start_connection = start
                wire.end_connection = end

    def find_collisions(self, go_to_x, go_to_y):
        collision = self.canvas.find_overlapping(go_to_x - self.r, go_to_y - self.r, go_to_x + self.r,
                                                 go_to_y + self.r)
        collision = list(collision)
        if self.collision_id in collision:
            collision.remove(self.collision_id)
        for wire_label in self.canvas.wire_label_tags:
            if wire_label in collision:
                collision.remove(wire_label)
        for wire in self.canvas.wires:
            tag = wire.line
            if tag in collision:
                collision.remove(tag)
        return collision

    def is_illegal_move(self, new_x):
        for connection in list(filter(lambda x: (x is not None and x != self),
                                      [w.end_connection for w in self.wires] + [w.start_connection for w in
                                                                                self.wires])):
            if connection.side == "spider" and abs(new_x - connection.location[0]) < 2 * self.r:
                return True
            if connection.side == "left":
                if new_x + self.r >= connection.location[0] - connection.width_between_boxes:
                    return True
            if connection.side == "right":
                if new_x - self.r <= connection.location[0] + connection.width_between_boxes:
                    return True
        return False

    def remove_wire(self, wire=None):
        if wire and wire in self.wires:
            self.wires.remove(wire)
            self.has_wire = len(self.wires) > 0
