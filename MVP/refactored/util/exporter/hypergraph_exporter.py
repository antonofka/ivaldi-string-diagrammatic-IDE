from MVP.refactored.backend.hypergraph.hypergraph_manager import HypergraphManager
from MVP.refactored.util.exporter.exporter import Exporter


class HypergraphExporter(Exporter):

    def create_file_content(self, filename: str) -> dict:
        """Create the hypergraph dictionary content of the file to be exported"""
        graph_id = self.canvas.id
        graph = HypergraphManager.get_graph_by_id(graph_id)

        return graph.to_dict()
