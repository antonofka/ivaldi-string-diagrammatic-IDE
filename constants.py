import os

# directory locations
ROOT_DIR = os.path.dirname(__file__)
ASSETS_DIR = os.path.join(ROOT_DIR, "assets/")
CONF_DIR = ROOT_DIR + "/MVP/refactored/conf/"

# file locations
FUNCTIONS_CONF = CONF_DIR + "functions_conf.json"
BOXES_CONF = CONF_DIR + "boxes_conf.json"

# box shapes
RECTANGLE = "rectangle"
TRIANGLE = "triangle"
AND_GATE = "and_gate"
OR_GATE = "or_gate"
XOR_GATE = "xor_gate"

SHAPES = [RECTANGLE, TRIANGLE, AND_GATE, OR_GATE, XOR_GATE]

# box sides
LEFT = "left"
RIGHT = "right"

# colors
SELECT_COLOR = "green"
PRIMARY_SEARCH_COLOR = "cyan"
SECONDARY_SEARCH_COLOR = "orange"
BLACK = "black"
WHITE = "white"


SPIDER = "spider"
