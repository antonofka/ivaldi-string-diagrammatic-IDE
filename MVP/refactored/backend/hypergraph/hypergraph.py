from MVP.refactored.backend.hypergraph.node import Node
import networkx as nx
import matplotlib.pyplot as plt


class Hypergraph(Node):

    def __init__(self, hypergraph_id=None, inputs=None, outputs=None, nodes=None):
        super().__init__(hypergraph_id, inputs, outputs)
        if nodes is None:
            nodes = []
        self.nodes = nodes
        self.set_hypergraph_io()

    def add_node(self, node: Node) -> None:
        if node in self.nodes:
            raise ValueError("Node already exists")
        self.nodes.append(node)
        self.set_hypergraph_io()

    def get_node_by_input(self, input_id: int) -> Node | None:
        for node in self.nodes:
            if input_id in node.inputs:
                return node
        return None

    def get_node_by_output(self, output_id: int) -> Node | None:
        for node in self.nodes:
            if output_id in node.outputs:
                return node
        return None

    def get_node_children_by_id(self, node_id: int) -> list[Node]:
        return self.get_node_children_by_node(self.get_node(node_id))

    def get_node_children_by_node(self, required_node: Node) -> list[Node]:
        children = []
        for node in self.nodes:
            if any(n in node.inputs for n in required_node.outputs):
                children.append(node)
        return children

    def get_node_parents_by_id(self, node_id: int) -> list[Node]:
        return self.get_node_parents_by_node(self.get_node(node_id))

    def get_node_parents_by_node(self, required_node: Node) -> list[Node]:
        parents = []
        for node in self.nodes:
            if any(n in node.outputs for n in required_node.inputs):
                parents.append(node)
        return parents

    def add_nodes(self, nodes: [Node]) -> None:
        for node in nodes:
            self.add_node(node)

    def get_node(self, node_id: int) -> Node | None:
        for node in self.nodes:
            if node.id == node_id:
                return node
        return None

    def remove_node(self, node: Node) -> None:
        self.nodes.remove(node)

    def set_hypergraph_io(self) -> None:
        all_inputs = set()
        all_outputs = set()

        for node in self.nodes:
            all_inputs.update(node.inputs)
            all_outputs.update(node.outputs)

        self.inputs = list(all_inputs - all_outputs)
        self.outputs = list(all_outputs - all_inputs)

    def is_valid(self) -> bool:
        if not self.inputs or not self.outputs or not self.nodes:
            return False

        node_inputs = set()
        node_outputs = set()

        for node in self.nodes:
            if not node.is_valid():
                return False

            node_inputs.update(node.inputs)
            node_outputs.update(node.outputs)

        invalid_inputs = node_inputs - set(self.inputs) - node_outputs
        if invalid_inputs:
            return False

        invalid_outputs = node_outputs - set(self.outputs) - node_inputs
        if invalid_outputs:
            return False

        if not self.is_connected():
            return False

        has_no_cycles = self.has_no_cycles()
        if not has_no_cycles:
            return False

        return True

    def is_connected(self) -> bool:
        visited = set()
        self.explore_connected(self.nodes[0], visited)

        return len(visited) == len(self.nodes)

    def explore_connected(self, node, visited):
        """Helper function to perform DFS for connectivity check."""
        if node in visited:
            return
        visited.add(node)

        for node_output in node.outputs:
            for other_node in self.nodes:
                if node_output in other_node.inputs and other_node not in visited:
                    self.explore_connected(other_node, visited)

        for node_input in node.inputs:
            for other_node in self.nodes:
                if node_input in other_node.outputs and other_node not in visited:
                    self.explore_connected(other_node, visited)

    def has_no_cycles(self) -> bool:
        explored_nodes = set()
        current_path = set()

        for current_node in self.nodes:
            if current_node not in explored_nodes:
                if not self.depth_first_search(current_node, explored_nodes, current_path):
                    return False
        return True

    def depth_first_search(self, node, visited, current_path) -> bool:
        if node in current_path:
            return False
        if node in visited:
            return True

        visited.add(node)
        current_path.add(node)

        for output in node.outputs:
            for other_node in self.nodes:
                if output in other_node.inputs:
                    if not self.depth_first_search(other_node, visited, current_path):
                        return False

        current_path.remove(node)
        return True

    def to_dict(self) -> dict:
        hypergraph_dict = super().to_dict()
        hypergraph_dict["nodes"] = [node.to_dict() for node in self.nodes]
        return hypergraph_dict

    def visualize(self):
        g = nx.DiGraph()
        for node in self.nodes:
            g.add_node(node.id, label="N_" + str(node.id)[-6:])
            for output in node.outputs:
                for other_node in self.nodes:
                    if output in other_node.inputs:
                        g.add_edge(node.id, other_node.id, label=str(output)[-6:])

        start_node_id = "input"
        g.add_node(start_node_id)
        for input_wire in self.inputs:
            for node in self.nodes:
                if input_wire in node.inputs:
                    g.add_edge(start_node_id, node.id, label=str(input_wire)[-6:])

        end_node_id = "output"
        g.add_node(end_node_id)
        for output_wire in self.outputs:
            for node in self.nodes:
                if output_wire in node.outputs:
                    g.add_edge(node.id, end_node_id, label=str(output_wire)[-6:])

        fig, ax = plt.subplots(figsize=(10, 5))
        pos = nx.spring_layout(g)

        nx.draw_networkx_nodes(g, pos, ax=ax, nodelist=[node.id for node in self.nodes],
                               node_size=700, node_color='lightblue', alpha=0.8)
        nx.draw_networkx_edges(g, pos, ax=ax, arrowstyle="->", arrowsize=20, edge_color="black")
        edge_labels = {(u, v): d['label'] for u, v, d in g.edges(data=True)}
        nx.draw_networkx_edge_labels(g, pos, edge_labels=edge_labels, ax=ax)
        nx.draw_networkx_labels(g, pos, labels={n: g.nodes[n].get('label', n) for n in g.nodes()}, ax=ax)

        ax.set_title(f"Hypergraph ID: {self.id}")
        ax.axis('off')

        return fig

    def __str__(self) -> str:
        node_descriptions = [f"Node ID: {node.id}, Inputs: {node.inputs}, Outputs: {node.outputs}" for node in
                             self.nodes]

        # Format the node descriptions into a single string
        nodes_str = "\n".join(node_descriptions)

        return (f"Hypergraph ID: {self.id}\n"
                f"Inputs: {self.inputs}\n"
                f"Outputs: {self.outputs}\n"
                f"Nodes:\n{nodes_str}")
