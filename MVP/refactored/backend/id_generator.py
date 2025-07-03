class IdGenerator:
    id_counter = -1

    @staticmethod
    def id():
        IdGenerator.id_counter += 1  # TODO temp solution
        return IdGenerator.id_counter
