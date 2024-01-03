# -*- coding: utf-8 -*-

"""my project.

"""

import sys
from os import path


VERSION = (0, 0, 1)
__version__ = ".".join(map(str, VERSION))


__setup = False
__depth = 1
while True:
    try:
        stack = sys._getframe(__depth)
        if stack.f_globals.get("__file__"):
            path.basename(stack.f_globals.get("__file__"))  # type: ignore
        __depth += 1
    except ValueError:
        break

__setup = path.basename(stack.f_globals.get("__file__")) == "setup.py"  # type: ignore

if not __setup:
    # fix "grpc_tools" generated code importing issue
    from .config import BASE_DIR

    sys.path.append(BASE_DIR)

    from .routes import routing_table, static_table
