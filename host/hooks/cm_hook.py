"""Pre-0.8.0 name of sqrm8_hook.py, kept so a checkout updated with `git pull` keeps working until its hooks are
reinstalled (tools/install.sh, or `hooks check` saying "needs reinstall"). Without it Claude Code would run a
missing file, and python exits 2 for that: the code a Stop hook uses to keep Claude from stopping.
Same contract as sqrm8_hook.py: tiny, silent, always exits 0. Remove once no 0.7.x install is left.
"""
import os
import sys

if __name__ == "__main__":
    try:
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from companion.hookclient import run_hook
    except BaseException:
        try:
            sys.stdin.buffer.read()
        except BaseException:
            pass
        os._exit(0)
    run_hook(sys.argv[1:])
