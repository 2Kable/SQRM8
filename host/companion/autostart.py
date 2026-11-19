"""Start the tray app at login: macOS LaunchAgent, Linux XDG autostart entry, Windows HKCU Run key.

    enable() -> str     install the entry (and first disable+stop the old headless service, if any); returns a
                        human sentence saying what was done (for a notification / the CLI)
    disable() -> str    remove the entry
    is_enabled() -> bool
    legacy_service_installed() -> bool   the headless daemon from tools/install.sh is still set up
    migrate_legacy() -> str   replace a start-at-login entry left under the pre-0.8.0 name (Claudius Maximus)

The entry runs `self_command() + ["app"]`. Two daemons would fight over the single-instance lock (the loser
just exits, but then the tray app shows "another daemon is running"), hence the legacy-service handling.

Deliberately not done: `launchctl bootstrap` on enable (RunAtLoad would start a second app right now, next to
the one calling us) and `launchctl bootout` on disable (would kill the running app if launchd started it). The
plist is picked up at the next login and simply ignored once removed. The same goes for Linux: nothing is
launched now, the .desktop file is read at the next login.

When $HOME is not the real home directory (tests, like tools/install.sh's test mode) launchctl / systemctl
are never called.
"""
from __future__ import annotations

import logging
import os
import plistlib
import subprocess
import sys

from . import hostos

log = logging.getLogger("companion.autostart")

APP_LABEL = "com.sqrm8.app"
DESKTOP_NAME = "sqrm8.desktop"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_VALUE = "SQRM8"
# The same entries before 0.8.0, when the app was called Claudius Maximus. Left in place they would start the
# old program (or a path that no longer exists) at login next to the new one.
LEGACY_APP_LABEL = "com.claudius-maximus.app"
LEGACY_DESKTOP_NAME = "claudius-maximus.desktop"
LEGACY_RUN_VALUE = "ClaudiusMaximus"


# ---------------------------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------------------------
def app_command() -> list[str]:
    """argv that starts the tray app. Windows, not frozen: pythonw (no console window) and a -c bootstrap,
    because a Run entry has no working directory to find the `companion` package from."""
    cmd = hostos.self_command() + ["app"]
    if hostos.IS_WINDOWS and not hostos.is_frozen():
        py = cmd[0]
        w = os.path.join(os.path.dirname(py), "pythonw.exe")
        if os.path.exists(w):
            py = w
        boot = (f"import sys; sys.path.insert(0, {hostos.package_root()!r}); "
                "from companion.__main__ import main; sys.exit(main(['app']))")
        cmd = [py, "-c", boot]
    return cmd


def mac_unstable_location(path: str | None = None) -> str:
    """macOS: why the running .app can't be the target of a login item ("" if it can). Opened from the .dmg
    it runs from /Volumes/... (gone after eject); opened from ~/Downloads with the quarantine flag, Gatekeeper
    App Translocation runs it from a random read-only /private/var/folders/.../AppTranslocation/... copy. A
    LaunchAgent pointing there would fail at the next login."""
    p = path or (hostos.self_command()[0] if hostos.is_frozen() else "")
    if "/AppTranslocation/" in p:
        return "it runs from a temporary App Translocation copy"
    if p.startswith("/Volumes/"):
        return "it runs from the disk image"
    return ""


def _win_profile_dir() -> str | None:
    """The account's profile folder from the shell (independent of HOME/USERPROFILE overrides)."""
    try:
        import ctypes
        buf = ctypes.create_unicode_buffer(1024)
        if ctypes.windll.shell32.SHGetFolderPathW(None, 40, None, 0, buf) == 0:   # CSIDL_PROFILE
            return buf.value or None
    except Exception:
        pass
    return None


def _uid() -> int:
    return os.getuid() if hasattr(os, "getuid") else 0


def _real_home() -> bool:
    """False when HOME points somewhere else than the account's home (tests): never touch launchctl/systemctl."""
    try:
        if sys.platform == "win32":
            real = _win_profile_dir() or os.environ.get("USERPROFILE") or os.path.expanduser("~")
        else:
            import pwd
            real = pwd.getpwuid(os.getuid()).pw_dir
        return os.path.normcase(os.path.realpath(real)) == os.path.normcase(os.path.realpath(hostos.home()))
    except Exception:
        return True


def _run(cmd: list[str]) -> int:
    if not _real_home():
        log.info("test mode (HOME is not the real home): not running %s", " ".join(cmd))
        return 0
    try:
        return subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, timeout=20).returncode
    except (OSError, subprocess.SubprocessError) as e:
        log.warning("%s failed: %s", cmd[0], e)
        return -1


def _write_atomic(path: str, data: bytes) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "wb") as f:
        f.write(data)
    os.replace(tmp, path)


def plist_path(legacy: bool = False) -> str:
    label = LEGACY_APP_LABEL if legacy else APP_LABEL
    return os.path.join(hostos.home(), "Library", "LaunchAgents", f"{label}.plist")


def desktop_path(legacy: bool = False) -> str:
    base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(hostos.home(), ".config")
    return os.path.join(base, "autostart", LEGACY_DESKTOP_NAME if legacy else DESKTOP_NAME)


def plist_bytes(cmd: list[str] | None = None) -> bytes:
    cmd = cmd or app_command()
    d = {"Label": APP_LABEL, "ProgramArguments": cmd, "RunAtLoad": True, "KeepAlive": False,
         "ProcessType": "Interactive", "LimitLoadToSessionType": "Aqua"}
    cwd = hostos.self_cwd()
    if cwd:
        d["WorkingDirectory"] = cwd
    return plistlib.dumps(d)


def _desktop_quote(arg: str) -> str:
    """Desktop Entry spec Exec quoting."""
    if arg and not any(c in arg for c in ' \t\n"\'\\><~|&;$*?#()`'):
        return arg.replace("%", "%%")
    esc = arg.replace("\\", "\\\\").replace('"', '\\"').replace("`", "\\`").replace("$", "\\$")
    return '"' + esc.replace("%", "%%") + '"'


def desktop_bytes(cmd: list[str] | None = None) -> bytes:
    cmd = cmd or app_command()
    lines = ["[Desktop Entry]", "Type=Application", f"Name={hostos.APP_NAME}",
             "Comment=Desk companion for Claude Code (tray app)",
             "Exec=" + " ".join(_desktop_quote(a) for a in cmd), "Icon=sqrm8", "Terminal=false",
             "X-GNOME-Autostart-enabled=true", "X-KDE-autostart-after=panel"]
    cwd = hostos.self_cwd()
    if cwd:
        lines.append(f"Path={cwd}")
    return ("\n".join(lines) + "\n").encode()


def _winreg():
    import winreg  # noqa: PLC0415 (Windows only)
    return winreg


def windows_command(cmd: list[str] | None = None) -> str:
    return subprocess.list2cmdline(cmd or app_command())


# ---------------------------------------------------------------------------------------------
# the old headless service (tools/install.sh)
# ---------------------------------------------------------------------------------------------
def _service_set_up(legacy: bool) -> bool:
    """The headless daemon service under the current (legacy=False) or pre-0.8.0 name is set up: LaunchAgent
    plist present, or systemd unit file present and enabled/active (a unit merely left on disk, disabled, doesn't
    count)."""
    p = hostos.service_path(legacy)
    if not p or not os.path.exists(p):
        return False
    if hostos.IS_LINUX and _real_home():
        unit = hostos.LEGACY_SERVICE_UNIT if legacy else hostos.SERVICE_UNIT
        try:
            en = subprocess.run(["systemctl", "--user", "is-enabled", unit],
                                capture_output=True, text=True, timeout=10).stdout.strip()
            ac = subprocess.run(["systemctl", "--user", "is-active", unit],
                                capture_output=True, text=True, timeout=10).stdout.strip()
            return en in ("enabled", "enabled-runtime", "linked") or ac in ("active", "activating")
        except (OSError, subprocess.SubprocessError):
            return True
    return True


def legacy_service_installed() -> bool:
    """The headless daemon of a script install is set up, under its current or its pre-0.8.0 name."""
    return _service_set_up(False) or _service_set_up(True)


def disable_legacy_service() -> str:
    """Stop and disable the headless daemon (current and pre-0.8.0 names) so the app's daemon can take over.
    Returns what was done ("" if nothing). macOS: bootout + rename the plist to *.plist.disabled-by-app (launchd
    ignores it, the user can rename it back). Linux: systemctl --user disable --now (the unit file stays)."""
    msgs = []
    for legacy in (False, True):
        if not _service_set_up(legacy):
            continue
        p = hostos.service_path(legacy)
        if hostos.IS_MAC:
            label = hostos.LEGACY_SERVICE_LABEL if legacy else hostos.SERVICE_LABEL
            _run(["launchctl", "bootout", f"gui/{_uid()}/{label}"])
            try:
                os.replace(p, p + ".disabled-by-app")
            except OSError as e:
                log.warning("cannot move %s aside: %s", p, e)
            msgs.append(f"stopped and disabled the headless LaunchAgent {label} ({p}.disabled-by-app)")
        else:
            unit = hostos.LEGACY_SERVICE_UNIT if legacy else hostos.SERVICE_UNIT
            _run(["systemctl", "--user", "disable", "--now", unit])
            msgs.append(f"stopped and disabled the headless systemd user service {unit}")
        log.info("%s", msgs[-1])
    return "; ".join(msgs)


def _legacy_entry_present() -> bool:
    """A start-at-login entry of the app under its pre-0.8.0 name exists."""
    if hostos.IS_WINDOWS:
        try:
            wr = _winreg()
            with wr.OpenKey(wr.HKEY_CURRENT_USER, RUN_KEY) as k:
                wr.QueryValueEx(k, LEGACY_RUN_VALUE)
                return True
        except OSError:
            return False
    return os.path.exists(plist_path(True) if hostos.IS_MAC else desktop_path(True))


def remove_legacy_entry() -> bool:
    """Delete the pre-0.8.0 start-at-login entry (no launchctl bootout: launchd may have started this very
    process from it). True if one was removed."""
    if not _legacy_entry_present():
        return False
    try:
        if hostos.IS_WINDOWS:
            wr = _winreg()
            with wr.OpenKey(wr.HKEY_CURRENT_USER, RUN_KEY, 0, wr.KEY_SET_VALUE) as k:
                wr.DeleteValue(k, LEGACY_RUN_VALUE)
        else:
            os.unlink(plist_path(True) if hostos.IS_MAC else desktop_path(True))
    except OSError as e:
        log.warning("cannot remove the old start-at-login entry: %s", e)
        return False
    log.info("removed the start-at-login entry of the app's old name (Claudius Maximus)")
    return True


def migrate_legacy() -> str:
    """At app start: an upgrade from 0.7.x leaves its start-at-login entry under the old name, pointing at the
    old program path. Replace it with this program's entry (start at login stays on). Returns what was done."""
    if not _legacy_entry_present():
        return ""
    if is_enabled():
        remove_legacy_entry()
        return "removed the start-at-login entry of the app's old name"
    return enable()   # writes this program's entry, then removes the old one


# ---------------------------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------------------------
def is_enabled() -> bool:
    if hostos.IS_MAC:
        return os.path.exists(plist_path())
    if hostos.IS_WINDOWS:
        try:
            wr = _winreg()
            with wr.OpenKey(wr.HKEY_CURRENT_USER, RUN_KEY) as k:
                v, _ = wr.QueryValueEx(k, RUN_VALUE)
                return bool(v)
        except OSError:
            return False
    return os.path.exists(desktop_path())


def enable(cmd: list[str] | None = None) -> str:
    """Start the app at login. `cmd` = the command to register instead of this program's (the updater
    registers the new version's). Raises OSError if the entry can't be written."""
    if hostos.IS_MAC:   # checked before retiring the legacy service: fail without side effects
        why = mac_unstable_location()
        if why:
            raise OSError(f"move {hostos.APP_NAME} to the Applications folder and open it from there first ({why})")
    notes = []
    legacy = disable_legacy_service()
    if legacy:
        notes.append(legacy)
    if hostos.IS_MAC:
        _write_atomic(plist_path(), plist_bytes(cmd))
        where = plist_path()
    elif hostos.IS_WINDOWS:
        wr = _winreg()
        with wr.CreateKey(wr.HKEY_CURRENT_USER, RUN_KEY) as k:
            wr.SetValueEx(k, RUN_VALUE, 0, wr.REG_SZ, windows_command(cmd))
        where = "HKCU\\" + RUN_KEY + "\\" + RUN_VALUE
    else:
        _write_atomic(desktop_path(), desktop_bytes(cmd))
        where = desktop_path()
    remove_legacy_entry()   # only once the new entry is written: never leave the user without one
    msg = f"{hostos.APP_NAME} will start at login ({where})"
    log.info("autostart enabled: %s", where)
    return "; ".join([msg] + notes)


def disable() -> str:
    if hostos.IS_WINDOWS:
        try:
            wr = _winreg()
            with wr.OpenKey(wr.HKEY_CURRENT_USER, RUN_KEY, 0, wr.KEY_SET_VALUE) as k:
                wr.DeleteValue(k, RUN_VALUE)
        except OSError:
            pass
    else:
        try:
            os.unlink(plist_path() if hostos.IS_MAC else desktop_path())
        except FileNotFoundError:
            pass
    remove_legacy_entry()   # off means off: the pre-0.8.0 entry would still start the old program
    log.info("autostart disabled")
    return f"{hostos.APP_NAME} will not start at login"


def describe() -> str:
    where = (plist_path() if hostos.IS_MAC else "HKCU\\" + RUN_KEY + "\\" + RUN_VALUE if hostos.IS_WINDOWS
             else desktop_path())
    s = f"autostart: {'enabled' if is_enabled() else 'disabled'} ({where})"
    if legacy_service_installed():
        s += f"\nheadless {hostos.service_name()} also installed: {hostos.installed_service_path()}" \
             " (enable autostart to replace it)"
    return s


if __name__ == "__main__":  # pragma: no cover
    print(describe(), file=sys.stdout)
