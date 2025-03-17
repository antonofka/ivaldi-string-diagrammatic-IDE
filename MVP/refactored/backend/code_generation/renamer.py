import ast

import astor  # Requires pip install astor


class Renamer(ast.NodeTransformer):
    def __init__(self, target_name: str = None, new_name: str = None):
        self.target_name = target_name
        self.new_name = new_name
        self.current_function_globals = set()
        self.current_function_params = set()
        self.global_vars = set()
        self.global_statements = set()
        self.function_names = set()

    def visit_Assign(self, node):
        if hasattr(node, "parent") and isinstance(node.parent, ast.Module):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.global_vars.add(target.id)
        self.generic_visit(node)

        return node

    def visit_FunctionDef(self, node):
        self.function_names.add(node.name)
        if node.name == self.target_name:
            node.name = self.new_name

        self.current_function_params = {arg.arg for arg in node.args.args}

        for stmt in node.body:
            if isinstance(stmt, ast.Global):
                stmt.names = [
                    self.new_name if name == self.target_name else name
                    for name in stmt.names
                ]
                self.global_statements.update(stmt.names)
                self.current_function_globals.update(stmt.names)

        self.generic_visit(node)

        self.current_function_globals.clear()
        self.current_function_params.clear()

        return node

    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == self.target_name:
            node.func.id = self.new_name
        self.generic_visit(node)
        return node

    def visit_Name(self, node):
        if (
                node.id == self.target_name
                and (
                node.id in self.current_function_globals
                or not self.current_function_params)
        ):
            node.id = self.new_name

        return node

    def refactor_code(self, code_str: str, target_name: str, new_name: str):
        if target_name:
            self.target_name = target_name
        if new_name:
            self.new_name = new_name
        tree = ast.parse(code_str)
        self.visit(tree)
        return astor.to_source(tree)

    def find_globals(self, code_str):
        tree = ast.parse(code_str)
        self._attach_parents(tree)
        self.visit(tree)

        all_globals = self.global_vars.union(self.global_statements)
        self.cleanup()
        return all_globals

    def find_function_names(self, code_str):
        tree = ast.parse(code_str)
        self.visit(tree)

        functions = set(self.function_names)
        self.cleanup()
        return functions

    def cleanup(self):
        self.global_vars.clear()
        self.global_statements.clear()
        self.function_names.clear()

    def _attach_parents(self, node, parent=None):
        node.parent = parent
        for child in ast.iter_child_nodes(node):
            self._attach_parents(child, node)
