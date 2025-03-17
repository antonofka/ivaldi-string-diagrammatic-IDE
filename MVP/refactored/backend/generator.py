class Generator:
    def __init__(self, id):
        self.id = id
        self.type = 0  # 0-atomic 1-compound None-undefined
        self.left = []
        self.right = []
        self.left_inner = []
        self.right_inner = []
        self.subset = []
        self.parent = None
        self.spiders = []
        self.operand = None

    def add_left(self, left):
        self.left.append(left)

    def add_right(self, right):
        self.right.append(right)

    def add_left_inner(self, left):
        self.left_inner.append(left)

    def add_right_inner(self, right):
        self.right_inner.append(right)

    def add_operand(self, operand):
        self.operand = operand

    def remove_operand(self):
        self.operand = None

    def add_type(self, type):
        self.type = type

    def remove_type(self):
        self.type = None

    def remove_all_left(self):
        self.left = []

    def remove_all_right(self):
        self.right = []

    def remove_left(self, connection=None):
        self.left.pop(connection[0])
        for i, resource in enumerate(self.left):
            resource[0] = i

    def remove_right(self, connection=None):
        self.right.pop(connection[0])
        for i, resource in enumerate(self.right):
            resource[0] = i

    def remove_left_inner(self, connection=None):
        self.left_inner.pop(connection[0])
        for i, resource in enumerate(self.left_inner):
            resource[0] = i

    def remove_right_inner(self, connection=None):
        self.right_inner.pop(connection[0])
        for i, resource in enumerate(self.right_inner):
            resource[0] = i

    def remove_left_atomic(self, connection_id):
        self.left.pop(connection_id)
        for i, resource in enumerate(self.left):
            resource[0] = i

    def remove_right_atomic(self, connection_id):
        self.right.pop(connection_id)
        for i, resource in enumerate(self.left):
            resource[0] = i

    def to_dict(self):
        return {
            "id": self.id,
            "type": self.type,
            "left": self.left,
            "right": self.right,
            "left_inner": self.left_inner,
            "right_inner": self.right_inner,
            "operand": self.operand
        }

    @classmethod
    def from_dict(cls, data):
        box = cls(data["id"])
        box.type = data.get("type")
        box.left = data.get("left", [])
        box.right = data.get("right", [])
        box.left_inner = data.get("left_inner", [])
        box.right_inner = data.get("right_inner", [])
        box.operand = data.get("operand")
        return box
