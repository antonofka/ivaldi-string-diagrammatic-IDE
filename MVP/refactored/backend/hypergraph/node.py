from __future__ import annotations

from importlib import import_module


class Node:

    def __init__(self, node_id=None, inputs=None, outputs=None):
        if node_id is None:
            node_id = id(self)
        if inputs is None:
            inputs = []
        if outputs is None:
            outputs = []
        self.id = node_id
        self.inputs = inputs
        self.outputs = outputs

    def get_children(self):
        module = import_module("MVP.refactored.backend.hypergraph.hypergraph_manager")
        HypergraphManager = getattr(module, "HypergraphManager")
        hypergraph = HypergraphManager.get_graph_by_node_id(self.id)
        return hypergraph.get_node_children_by_node(self)

    def get_parents(self):
        module = import_module("MVP.refactored.backend.hypergraph.hypergraph_manager")
        HypergraphManager = getattr(module, "HypergraphManager")
        hypergraph = HypergraphManager.get_graph_by_node_id(self.id)
        return hypergraph.get_node_parents_by_node(self)

    def add_input(self, input_id: int) -> None:
        if input_id in self.inputs or input_id in self.outputs:
            raise ValueError("Input already exists")

        self.inputs.append(input_id)

    def remove_input(self, input_id: int) -> None:
        self.inputs.remove(input_id)

    def add_output(self, output_id: int) -> None:
        if output_id in self.inputs or output_id in self.outputs:
            raise ValueError("Output already exists")

        self.outputs.append(output_id)

    def remove_output(self, output_id: int) -> None:
        self.outputs.remove(output_id)

    def is_valid(self) -> bool:
        return len(self.inputs) > 0 and len(self.outputs) > 0

    def has_input(self, input_id) -> bool:
        return input_id in self.inputs

    def has_output(self, output_id) -> bool:
        return output_id in self.outputs

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "inputs": self.inputs,
            "outputs": self.outputs,
        }

    def __str__(self) -> str:
        return (f"Node ID: {self.id}\n"
                f"Inputs: {self.inputs}\n"
                f"Outputs: {self.outputs}")

    def __eq__(self, other):
        if not isinstance(other, Node):
            return False
        return other.id == self.id

    def __hash__(self):
        return hash(self.id)
