import tkinter as tk

from MVP.refactored.backend.id_generator import IdGenerator
from MVP.refactored.backend.types.ActionType import ActionType
from MVP.refactored.frontend.canvas_objects.connection import Connection
from MVP.refactored.frontend.canvas_objects.types.connection_type import ConnectionType
import constants as const


class Spider(Connection):
    """
    Spider. A subclass of Connection.

    Used separately from Boxes and diagram input/output. They are a freely moving canvas widget, displayed as a circle.
    Its size can vary. It allows multiple wires to be connected to it.
    """
    def __init__(self, location, canvas, id_=None, connection_type=ConnectionType.GENERIC):
        """
        Spider constructor.

        :param location: Tuple of coordinates for creation. Ex: (10, 20)
        :param canvas: CustomCanvas object that Spider will be created on.
        :param id_: Optional id parameter
        :param connection_type: ConnectionType that will define the style of the Connection.
        """
        self.r = 10
        location = list(location)
        super().__init__(None, 0, const.SPIDER, location, canvas, self.r, connection_type=connection_type)
        self.canvas = canvas
        self.x = None
        self.y = None

        self.display_x = None
        self.display_y = None

        self.rel_x = None
        self.rel_y = None

        if not id_:
            self.id = IdGenerator.id()
        else:
            self.id = id_

        self.connections: list[Connection] = []
        self.wires = []
        self.receiver = canvas.main_diagram.receiver
        if self.receiver.listener and not self.canvas.is_search:
            self.receiver.receiver_callback(ActionType.SPIDER_CREATE, resource_id=self.id, canvas_id=canvas.id)

        self.is_snapped = False

        self.update_location(location)  # This can be removed if Connection has separate x and y coords like spider does

        self.bind_events()

    def is_spider(self):
        """
        Method to check if the Connection is a Spider.

        :return: True if the Connection is a Spider, False otherwise
        """
        return True

    def bind_events(self):
        """
        Bind events to circle created on CustomCanvas.

        :return: None
        """
        self.canvas.tag_bind(self.circle, '<ButtonPress-1>', lambda event: self.on_press())
        self.canvas.tag_bind(self.circle, '<B1-Motion>', self.on_drag)
        self.canvas.tag_bind(self.circle, '<ButtonPress-3>', self.show_context_menu)
        self.canvas.tag_bind(self.circle, '<Control-ButtonPress-1>', lambda event: self.on_control_press())
        self.canvas.tag_bind(self.circle, "<Enter>", lambda _: self.canvas.on_hover(self))
        self.canvas.tag_bind(self.circle, "<Leave>", lambda _: self.canvas.on_leave_hover())
        self.canvas.tag_bind(self.circle, '<Button-2>', lambda x: self.increment_type())

    def show_context_menu(self, event):
        """
        Create and display a context menu for the selected Spider.

        :param event: Event sent from keybind. Location used for context menu to be created at.
        :return: None
        """
        self.close_menu()
        self.context_menu = tk.Menu(self.canvas, tearoff=0)

        self.add_type_choice()

        self.context_menu.add_command(label="Delete Spider", command=self.delete)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="Cancel")

        self.context_menu.tk_popup(event.x_root, event.y_root)

    def delete(self, action=None):
        """
        Delete Spider.

        :param action: Specify if action is done for creating a sub-diagram.
        :return: None
        """
        [wire.delete(self) for wire in self.wires.copy()]
        self.canvas.spiders.remove(self)
        super().delete()
        if self.receiver.listener and not self.canvas.is_search:
            self.receiver.receiver_callback(ActionType.SPIDER_DELETE, resource_id=self.id, canvas_id=self.canvas.id)

    def close_menu(self):
        """
        Close context menu if exists.

        :return: None
        """
        if self.context_menu:
            self.context_menu.destroy()

    def add_wire(self, wire):
        """
        Add wire to Spider.

        This method adds a wire to the wires list if it's not already added.

        :param wire: Wire that will be added to wires.
        :return: None
        """
        if wire not in self.wires:
            self.wires.append(wire)
            self.has_wire = True

    def on_resize_scroll(self, event):
        """
        Handle resizing scroll keybind.

        Checks the event to see if Spider needs to be made smaller or larger.
        Checks for collisions with potential new size, if there are collisions then resizing is cancelled.
        Changes the size of the Spider according to event.

        :param event: Event object sent from key bind.
        :return: None
        """
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
        self.canvas.coords(self.circle, self.display_x - self.r, self.display_y - self.r, self.display_x + self.r,
                           self.display_y + self.r)

    # MOVING, CLICKING ETC.
    def on_press(self):
        """
        Handle button-1 press. (Left mouse click)

        Clears previously selected items and adds current Spider to new selection.

        :return: None
        """
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
        """
        Handle ctrl + button-1 press.

        Similar to .on_press(), but does not clear earlier selections.
        Selects/deselects based on whether Spider was selected or not.

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
        Handle Spider dragging.

        Uses is_illegal_move() to check for move legality. Checks if it is moving into the same x-axis as another
        existing widget and will snap the object to the closest free space in the same x-axis as the found widget.
        If Spider is already snapped it will also check for collision with other objects like other Spiders or Boxes
        and would not allow movement through them.

        :param event: Event object sent from key bind.
        :param from_configuration: Boolean stating if the drag call is coming due to canvas configuration.
        :return: None
        """
        if event.state & 0x4:
            return
        if self.canvas.pulling_wire:
            return

        log_ev_x, log_ev_y = self.canvas.convert_coords(event.x, event.y, to_logical=True)

        go_to_x = self.x
        go_to_y = log_ev_y
        move_legal = False

        if not self.is_illegal_move(log_ev_x, bypass=from_configuration):
            go_to_x = log_ev_x
            move_legal = True

        # snapping into place
        found = False
        if not from_configuration:
            for box in self.canvas.boxes:
                if (abs(box.x + box.get_logical_size(box.size)[0] / 2 - go_to_x) < box.get_logical_size(box.size)[0] / 2
                        + self.r and move_legal):
                    go_to_x = box.x + box.get_logical_size(box.size)[0] / 2
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

        self.align_wire_ends()

        self.is_snapped = found
        self.update_location((go_to_x, go_to_y))

        self.rel_x = round(self.display_x / self.canvas.winfo_width(), 4)
        self.rel_y = round(self.display_y / self.canvas.winfo_height(), 4)
        [w.update() for w in self.wires]

    def align_wire_ends(self):
        """
        Method used to check if the Spider has moved to the other side of a connected Spider and change variables
        accordingly.

        If the Spider has moved to the other side of a different Spider, then wire start and end connections
        will flip. Start connection becomes end connection and vice versa. This is used to keep the wire start and end
        connections on the left and right accordingly.

        :return: None
        """
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
        """
        Find collisions at the desired location.

        Takes x and y logical coordinates and checks the surrounding area, equal to the size of the Spider.
        Returns a list of canvas tags that are in the location. Wires are excluded from this.

        :param go_to_x: x coordinate for the center of the search.
        :param go_to_y: y coordinate for the center of the search.
        :return: List of ints.
        """
        go_to_x, go_to_y = self.canvas.convert_coords(go_to_x, go_to_y, to_display=True)
        collision = self.canvas.find_overlapping(go_to_x - self.r, go_to_y - self.r, go_to_x + self.r,
                                                 go_to_y + self.r)
        collision = list(collision)
        if self.circle in collision:
            collision.remove(self.circle)
        for wire_label in self.canvas.wire_label_tags:
            if wire_label in collision:
                collision.remove(wire_label)
        for wire in self.canvas.wires:
            tag = wire.line
            if tag in collision:
                collision.remove(tag)
        return collision

    def is_illegal_move(self, new_x, bypass=False):
        """
        Check if move to new_x is illegal.

        Checks if the Spider can move to new_x. It is illegal when the Spider is trying to move to the other side of a
        connected Connection. It is legal when a Spider is trying to cross over to the other side of a connected Spider,
        but illegal when trying to go into the same x-axis as the connected Spider.

        :param new_x: logical x coordinate that Spider is trying to move to.
        :param bypass: If legality check should be bypassed.
        :return: boolean
        """
        if bypass:
            return False
        for connection in list(filter(lambda x: (x is not None and x != self),
                                      [w.end_connection for w in self.wires] + [w.start_connection for w in
                                                                                self.wires])):
            if connection.side == const.SPIDER and abs(new_x - connection.location[0]) < 2 * self.r:
                return True
            if connection.side == const.LEFT:
                if new_x + self.r >= connection.location[0] - connection.width_between_boxes:
                    return True
            if connection.side == const.RIGHT:
                if new_x - self.r <= connection.location[0] + connection.width_between_boxes:
                    return True
        return False

    def remove_wire(self, wire=None):
        """
        Remove wire from Spider.

        If possible remove the given wire from the Spider.

        :param wire: Wire to be removed.
        :return: None
        """
        if wire and wire in self.wires:
            self.wires.remove(wire)
            self.has_wire = len(self.wires) > 0

    def update_location(self, new_location):
        """
        Move the Spider to the given location.

        Takes a coordinate logical location and moves Spider to the given location on the canvas.

        :param new_location: tuple or list of logical coordinates. (x, y)
        :return: None
        """
        self.x, self.y = new_location

        super().update_location(new_location)
        self.display_x, self.display_y = self.display_location

        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        if self.canvas.winfo_width() <= 1:
            width = self.canvas.main_diagram.custom_canvas.winfo_width()
            height = self.canvas.main_diagram.custom_canvas.winfo_height()

        self.rel_x = round(self.display_x / width, 4)
        self.rel_y = round(self.display_y / height, 4)
