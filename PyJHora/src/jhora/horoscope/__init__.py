import os
import sys
_DIR = os.path.dirname(os.path.abspath(__file__))
path_root = os.path.dirname(os.path.dirname(_DIR))
if path_root not in sys.path:
    sys.path.append(str(path_root))
