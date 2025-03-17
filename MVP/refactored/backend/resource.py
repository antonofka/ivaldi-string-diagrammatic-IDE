class Resource:
    def __init__(self, id):
        self.id = id
        self.connections = []
        self.spider = False
        self.spider_connection = None
        self.parent = None

    def add_connection(self, connection):
        self.connections.append(connection)

    def remove_connection(self, connection):
        if connection in self.connections:
            self.connections.remove(connection)

    def to_dict(self):
        return {
            "id": self.id,
            "connections": self.connections
        }

    @classmethod
    def from_dict(cls, data):
        resource = cls(data["id"])
        resource.connections = data.get("connections")
        return resource
