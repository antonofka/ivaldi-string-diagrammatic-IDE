import os
from inspect import signature


def get_predefined_functions() -> dict:
    predefined_functions = {}
    functions_path = os.path.join(os.path.dirname(__file__), "./predefined/")
    dirs_and_files = os.listdir(functions_path)
    for name in dirs_and_files:
        full_path = os.path.join(functions_path, name)
        if os.path.isfile(full_path):
            with open(full_path, "r") as file:
                function_name = name.replace(".py", "").replace("_", " ")
                predefined_functions[function_name] = file.read()
    return predefined_functions


functions = get_predefined_functions()


class BoxFunction:
    def __init__(self, name, code=None):
        self.name = name
        if name in functions:
            self.code: str = functions[name]
        elif code is not None:
            self.code: str = code
        else:
            raise ValueError("Should be specified function code or name of predefined function")
        local = {}
        exec(self.code, {}, local)
        self.function = local["invoke"]
        self.meta = local["meta"]

    def __call__(self, *args):
        return self.function(*args)

    def count_inputs(self):
        sig = signature(self.code)
        params = sig.parameters
        count = len(params)
        if params["self"]:
            count -= 1
        return count

    def __eq__(self, other):
        if isinstance(other, BoxFunction):
            return self.code == other.code
        return False

    def __hash__(self):
        return hash(self.code)

    def __str__(self):
        return self.name
