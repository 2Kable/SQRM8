"""Idempotently add / remove the SQRM8 hooks + statusLine wrapper in ~/.claude/settings.json.

    python sqrm8_settings.py install   --root <project root> --python <venv python> [--no-statusline]
    python sqrm8_settings.py uninstall
    python sqrm8_settings.py check      (exit 0 if installed, 3 if under the pre-0.8.0 names)

Shim: the implementation is host/companion/hooksetup.py (so the frozen desktop app has it too; see its
docstring for the backup / manifest / statusLine-chaining behaviour). Everything is re-exported here.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from companion.hooksetup import *  # noqa: E402,F401,F403
from companion.hooksetup import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
