from unittest import TestCase

from MVP.refactored.backend.box_functions.box_function import BoxFunction

add = '''
def add(*numbers: list) -> int:
    if len(numbers) < 2:
        raise ValueError("Numbers amount should be at least 2")
    return sum(numbers)
'''

copy = '''
def copy(x) -> list:
    return [x, x]
'''

subtract = '''
def subtract(*numbers: list) -> int:
    if len(numbers) < 2:
        raise ValueError("Numbers amount should be at least 2")
    return numbers[0] - sum(numbers[1:])
'''

integral_code = '''
def compute_integral(f, a, b, n=1000):
    h = (b - a) / n
    total = 0.5 * (f(a) + f(b))
    for i in range(1, n):
        total += f(a + i * h)
    return total * h

def integral(f, a, b, n=1000):
    return compute_integral(f, a, b, n)
'''

pow_code = '''
def pow(base, exponent):
    return base ** exponent
'''


class TestBoxFunction(TestCase):

    def setUp(self):
        self.box_add = BoxFunction(main_function_name="add", file_code=add)
        self.box_subtract = BoxFunction(main_function_name="subtract", file_code=subtract)
        self.box_copy = BoxFunction(main_function_name="copy", file_code=copy)
        self.box_integral = BoxFunction(main_function_name="compute_integral", file_code=integral_code)
        self.box_pow = BoxFunction(main_function_name="pow", file_code=pow_code)

    def test_initialization_name_add(self):
        self.assertEqual(self.box_add.name, "add")

    def test_initialization_name_subtract(self):
        self.assertEqual(self.box_subtract.name, "subtract")

    def test_initialization_name_copy(self):
        self.assertEqual(self.box_copy.name, "copy")

    def test_initialization_name_integral(self):
        self.assertEqual(self.box_integral.name, "integral")

    def test_initialization_name_pow(self):
        self.assertEqual(self.box_pow.name, "pow")

    def test_initialization_main_function_add(self):
        expected_main_function = 'def invoke(*numbers: list) -> int:\n' \
                                 '    if len(numbers) < 2:\n' \
                                 "        raise ValueError('Numbers amount should be at least 2')\n" \
                                 '    return sum(numbers)\n'
        self.assertEqual(self.box_add.main_function, expected_main_function)

    def test_initialization_main_function_subtract(self):
        expected_main_function = 'def invoke(*numbers: list) -> int:\n' \
                                 '    if len(numbers) < 2:\n' \
                                 "        raise ValueError('Numbers amount should be at least 2')\n" \
                                 '    return numbers[0] - sum(numbers[1:])\n'
        self.assertEqual(self.box_subtract.main_function, expected_main_function)

    def test_initialization_main_function_copy(self):
        expected_main_function = 'def invoke(x) -> list:\n' \
                                 '    return [x, x]\n'
        self.assertEqual(self.box_copy.main_function, expected_main_function)

    def test_initialization_main_function_integral(self):
        expected_main_function = 'def integral(f, a, b, n=1000):\n' \
                                 '    return compute_integral(f, a, b, n)\n'
        self.assertEqual(self.box_integral.main_function, expected_main_function)

    def test_initialization_main_function_pow(self):
        expected_main_function = 'def pow(base, exponent):\n' \
                                 '    return base ** exponent\n'
        self.assertEqual(self.box_pow.main_function, expected_main_function)

    def test_initialization_helper_functions_add(self):
        expected_helpers = []
        self.assertEqual(self.box_add.helper_functions, expected_helpers)

    def test_initialization_helper_functions_subtract(self):
        expected_helpers = []
        self.assertEqual(self.box_subtract.helper_functions, expected_helpers)

    def test_initialization_helper_functions_copy(self):
        expected_helpers = []
        self.assertEqual(self.box_copy.helper_functions, expected_helpers)

    def test_initialization_helper_functions_integral(self):
        expected_helpers = ['def compute_integral(f, a, b, n=1000):\n'
                            '    h = (b - a) / n\n'
                            '    total = 0.5 * (f(a) + f(b))\n'
                            '    for i in range(1, n):\n'
                            '        total += f(a + i * h)\n'
                            '    return total * h\n']

        self.assertEqual(self.box_integral.helper_functions, expected_helpers)

    def test_initialization_helper_functions_pow(self):
        expected_helpers = []
        self.assertEqual(self.box_pow.helper_functions, expected_helpers)

    def test_initialization_imports_add(self):
        expected_imports = ['import math\n']
        self.assertEqual(self.box_add.imports, expected_imports)

    def test_initialization_imports_subtract(self):
        expected_imports = ['import math\n']
        self.assertEqual(self.box_subtract.imports, expected_imports)

    def test_initialization_imports_copy(self):
        expected_imports = []
        self.assertEqual(self.box_copy.imports, expected_imports)

    def test_initialization_imports_integral(self):
        expected_imports = []
        self.assertEqual(self.box_integral.imports, expected_imports)

    def test_initialization_imports_pow(self):
        expected_imports = []
        self.assertEqual(self.box_pow.imports, expected_imports)
