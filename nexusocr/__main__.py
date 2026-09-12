"""
CLI execution module for python -m nexusocr.
"""

import sys
from nexusocr.interfaces.cli.main import main

if __name__ == "__main__":
    sys.exit(main())
