import math


def invoke(*numbers: list) -> int:
    if len(numbers) < 2:
        raise ValueError("Numbers amount should be at least 2")
    return numbers[0] - sum(numbers[1:])


meta = {
    "name": "Subtract",
    "min_args": 2,
    "max_args": math.inf,
}
