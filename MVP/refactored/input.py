class Input:
    def __init__(self, id_=None):
        if not id_:
            self.id = id(self)
        else:
            self.id = id_
        self.value: int | None = None
        self.wire = None
        self.has_wire = False

    def add_wire(self, wire):
        if not self.has_wire and self.wire is None:
            self.wire = wire
            self.has_wire = True

    def remove_wire(self):
        if self.wire:
            self.wire = None
            self.has_wire = False
