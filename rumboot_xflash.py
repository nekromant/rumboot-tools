#!/usr/bin/env python3
# PYTHON_ARGCOMPLETE_OK

import sys
from rumboot.flashing import rumboot_start_flashing

if __name__ == "__main__":
    sys.exit(rumboot_start_flashing())
