"""SQRM8 — Claude Code statusLine wrapper.

Installed as the user's `statusLine.command` (host/hooks/sqrm8_settings.py):
    "<root>/host/.venv/bin/python" -I -S "<root>/host/hooks/sqrm8_statusline.py"
(a frozen desktop app installs `"<exe>" statusline` instead, which runs the same code).

The logic lives in host/companion/hookclient.py (`statusline_main`): record the plan limits Claude Code gives
the status line to ~/.sqrm8/statusline.json, send a StatusLine datagram to the daemon, then run the
user's previous statusLine command (saved in ~/.sqrm8/statusline-chain.json) and print its output.
Always exits 0.
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
