"""Pre-0.8.0 name of sqrm8_statusline.py, kept so a checkout updated with `git pull` keeps its status line until
its hooks are reinstalled (see cm_hook.py). Same contract as sqrm8_statusline.py. Remove once no 0.7.x install
is left.
"""
import os
import sys

if __name__ == "__main__":
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from companion.hookclient import run_statusline
    except BaseException:
        sys.exit(0)
    run_statusline()
