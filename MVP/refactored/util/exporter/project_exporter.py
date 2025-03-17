import json
import time
from tkinter import messagebox

from MVP.refactored.frontend.canvas_objects.connection import Connection
from MVP.refactored.frontend.canvas_objects.wire import Wire
from constants import *

from MVP.refactored.util.exporter.exporter import Exporter


class ProjectExporter(Exporter):

    def __init__(self, canvas):
        super().__init__(canvas)

    def create_file_content(self, filename):
        return {"file_name": filename,
                "date": time.time(),
                "static_variables": self.get_static_variables(),
                "main_canvas": self.create_canvas_dict(self.canvas)
                }

    @staticmethod
    def get_static_variables():
        variables = {
            "active_types": Connection.active_types,
            "defined_wires": Wire.defined_wires
        }
        return variables

    def create_canvas_dict(self, canvas):
        return {"boxes": self.create_boxes_list(canvas),
                "spiders": self.create_spiders_list(canvas),
                "io": self.create_io_dict(canvas),
                "wires": self.create_wires_list(canvas)}

    def create_wires_list(self, canvas):
        return [{"id": wire.id,
                 "start_c": self.get_connection(wire.start_connection),
                 "end_c": self.get_connection(wire.end_connection)
                 } for wire in canvas.wires]

    def create_spiders_list(self, canvas):
        spiders_list = []
        for spider in canvas.spiders:
            connections_list = self.get_connections(spider.connections)

            spider_d = {
                "id": spider.id,
                "x": spider.x,
                "y": spider.y,
                "connections": connections_list,
                "type": spider.type.name
            }
            spiders_list.append(spider_d)

        return spiders_list

    def create_io_dict(self, canvas):
        return {"inputs": self.get_connections(canvas.inputs),
                "outputs": self.get_connections(canvas.outputs)}

    def create_boxes_list(self, canvas):
        boxes_list = []
        for box in canvas.boxes:
            d = {
                "id": box.id,
                "x": box.x,
                "y": box.y,
                "size": box.size,
                "label": box.label_text,
                "connections": self.get_connections(box.connections),
                "sub_diagram": None,
                "locked": box.locked,
                "shape": box.shape
            }
            if box.sub_diagram:
                d["sub_diagram"] = self.create_canvas_dict(box.sub_diagram)
            boxes_list.append(d)

        return boxes_list

    def get_connections(self, c_list):
        return [self.get_connection(c) for c in c_list]

    @staticmethod
    def get_connection(connection):
        d = {"id": connection.id,
             "side": connection.side,
             "index": connection.index,
             "spider": connection.is_spider(),
             "box_id": None,
             "has_wire": connection.has_wire,
             "wire_id": None,
             "type": connection.type.name
             }
        if connection.box:
            d["box_id"] = connection.box.id
        if connection.wire:
            d["wire_id"] = connection.wire.id
        return d

    # BOX MENU LOGIC
    def export_box_to_menu(self, box):
        current = self.get_current_data()
        if box.label_text in current:
            messagebox.showinfo("Info", "Box with same label already in menu")
            return

        left_connections = 0
        right_connections = 0
        left_con_types = []
        right_con_types = []

        for c in box.connections:
            if c.side == "left":
                left_connections += 1
                left_con_types.append(c.type.name)
            elif c.side == "right":
                right_connections += 1
                right_con_types.append(c.type.name)

        new_entry = {
            "label": box.label_text,
            "left_c": left_connections,
            "right_c": right_connections,
            "left_c_types": left_con_types,
            "right_c_types": right_con_types,
            "shape": box.shape,
            "sub_diagram": None,
        }
        if box.sub_diagram:
            new_entry["sub_diagram"] = self.create_canvas_dict(box.sub_diagram)
        current[box.label_text] = new_entry

        with open(BOXES_CONF, "w") as outfile:
            json.dump(current, outfile, indent=4)

    @staticmethod
    def get_current_data():
        try:
            with open(BOXES_CONF, 'r') as json_file:
                data = json.load(json_file)
                return data
        except FileNotFoundError or IOError or json.JSONDecodeError:
            return {}

    def del_box_menu_option(self, box):
        current = self.get_current_data()
        current.pop(box)
        with open(BOXES_CONF, "w") as outfile:
            json.dump(current, outfile, indent=4)
