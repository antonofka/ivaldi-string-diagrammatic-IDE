from __future__ import annotations
from typing import TYPE_CHECKING
from MVP.refactored.backend.hypergraph.hypergraph import Hypergraph
from MVP.refactored.backend.hypergraph.node import Node

if TYPE_CHECKING:
    from MVP.refactored.frontend.components.custom_canvas import CustomCanvas


class HypergraphManager:
    hypergraphs: list[Hypergraph] = []

    @staticmethod
    def get_graph_by_node_id(node_id: int) -> Hypergraph | None:
        for hypergraph in HypergraphManager.hypergraphs:
            for node in hypergraph.nodes:
                if node.id == node_id:
                    return hypergraph
        return None

    @staticmethod
    def get_graph_by_id(hypergraph_id: int) -> Hypergraph | None:
        for graph in HypergraphManager.hypergraphs:
            if graph.id == hypergraph_id:
                return graph
        return None

    @staticmethod
    def modify_canvas_hypergraph(canvas: CustomCanvas) -> None:
        hypergraph = HypergraphManager.get_graph_by_id(canvas.id)

        if hypergraph:
            HypergraphManager.hypergraphs.remove(hypergraph)

        HypergraphManager.create_hypergraphs_from_canvas(canvas)

    @staticmethod
    def create_hypergraphs_from_canvas(canvas: CustomCanvas) -> None:
        hypergraph = Hypergraph(canvas.id)
        for box in canvas.boxes:
            node = Node(box.id)
            for connection in box.connections:
                if connection.side == "left" and connection.has_wire:
                    node.add_input(connection.wire.id)
                elif connection.has_wire:
                    node.add_output(connection.wire.id)
            hypergraph.add_node(node)

        if hypergraph.is_valid():
            HypergraphManager.hypergraphs.append(hypergraph)
