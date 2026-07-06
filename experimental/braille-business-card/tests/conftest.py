"""
Shared pytest fixtures/paths for the Braille Wedge Card test suite.

License: PolyForm Noncommercial 1.0.0
"""

import sys
from pathlib import Path

TESTS_DIR = Path(__file__).parent
PROJECT_ROOT = TESTS_DIR.parent
SCAD_FILE = PROJECT_ROOT / "Braille_Wedge_Card_STL_Generator.scad"

# Make sibling test modules (openscad_runner) importable regardless of the
# directory pytest is invoked from.
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))
