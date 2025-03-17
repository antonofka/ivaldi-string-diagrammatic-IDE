import json
from MVP.refactored.backend.generator import Generator
from MVP.refactored.backend.resource import Resource


class Diagram:
    def __init__(self):
        self.input = []
        self.output = []
        self.boxes = []
        self.resources = []
        self.spiders = []

    def add_resource(self, resource):
        self.resources.append(resource)

    def add_box(self, boxes):
        self.boxes.append(boxes)

    def remove_box(self, boxes):
        self.boxes.remove(boxes)

    def remove_resource(self, resources):
        if resources in self.resources:
            self.resources.remove(resources)

    def diagram_import(self, file_path):
        with open(file_path, 'r') as file:
            data = json.load(file)
            self._from_dict(data)

    def diagram_export(self, file_path):
        data = self._to_dict()
        with open(file_path, 'w') as file:
            json.dump(data, file, indent=4)

    def _to_dict(self):
        return {
            "input": self.input,
            "output": self.output,
            "boxes": [box.to_dict() for box in self.boxes],
            "resources": [resource.to_dict() for resource in self.resources]
        }

    def _from_dict(self, data):
        self.input = data.get("input", [])
        self.output = data.get("output", [])
        self.boxes = [Generator.from_dict(box_data) for box_data in data.get("boxes", [])]
        self.resources = [Resource.from_dict(resource_data) for resource_data in data.get("resources", [])]
