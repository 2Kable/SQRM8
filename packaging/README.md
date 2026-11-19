# Packaging the SQRM8 desktop app

The desktop app is one PyInstaller **onedir** build of `host/companion` (entry point `packaging/entry.py`: no
arguments = the tray app, any argument = the CLI, e.g. `hook`, `status`, `flash`). It bundles the firmware images
found in `host/companion/firmware/<board>/` at build time, so the app can flash or update the board by itself.

| OS | Build output | Installer | Release asset |
|---|---|---|---|
| Windows | `dist/SQRM8/SQRM8.exe` (no console) | Inno Setup, per-user, no admin | `SQRM8-<ver>-windows-x64.exe` |
| macOS | `dist/SQRM8.app` (menu bar only, no Dock icon) | drag-to-Applications `.dmg` | `SQRM8-<ver>-macos-arm64.dmg`, `-macos-x64.dmg` |
| Linux | `dist/sqrm8/sqrm8` | `.AppImage` + `.tar.gz` | `SQRM8-<ver>-linux-x64.AppImage`, `.tar.gz` |

Plus the raw firmware bundles `firmware-<board>-<fwver>.zip` (bootloader, partitions, boot_app0, app image and
`manifest.json` with the offsets) for flashing with esptool or the web flasher by hand.

## Build locally

Python 3.11+ and a checkout of the repo. Commands are run from the repo root.

```bash
python3 -m venv host/.venv
host/.venv/bin/pip install -e "host[dev]"                     # the app + PyInstaller + PlatformIO
host/.venv/bin/python tools/fw_bundle.py --board all --out host/companion/firmware   # optional: bundle firmware
host/.venv/bin/python packaging/make_icons.py                  # icons from companion.tray.icon (committed)
host/.venv/bin/pyinstaller --noconfirm packaging/sqrm8.spec   # -> dist/ (build/ is scratch)
```

Without the `fw_bundle.py` step the app builds fine but ships no firmware (the tray then offers no flashing).
On Windows the venv is `host\.venv\Scripts\` instead of `host/.venv/bin/`.

Then, per OS:

- **Linux**: `packaging/linux/make_appimage.sh dist/sqrm8 out` writes the `.tar.gz` (the onedir plus
  a `.desktop` file and icon) and, if `appimagetool` is on `PATH`, the `.AppImage`.
  The `.desktop` file says `Exec=sqrm8 app`: right for the AppImage (its runtime starts `AppRun`,
  and AppImage integrators rewrite `Exec`), but from the `.tar.gz` it only works if the binary is on `PATH`.
  Either `ln -s "$PWD/sqrm8/sqrm8" ~/.local/bin/` or put the absolute path in `Exec=`
  before copying the file to `~/.local/share/applications/` (and the icon to `~/.local/share/icons/`). The
  app's own "Start at login" entry always uses the absolute path (or `$APPIMAGE`).
- **macOS**: `packaging/macos/make_dmg.sh dist/SQRM8.app out/SQRM8-0.8.0-macos-arm64.dmg`.
  PyInstaller builds for the architecture of the Python you run it with: use an arm64 Python for Apple silicon
  and an x86_64 one (or an Intel Mac) for the x64 build.
- **Windows**: install [Inno Setup 6](https://jrsoftware.org/isinfo.php), then
  `"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DAppVersion=0.8.0 packaging\windows\installer.iss`
  (output in `dist\installer\`). The installer goes to `%LOCALAPPDATA%\Programs\SQRM8`, adds a "Start at
  login" task (HKCU `Run` value `SQRM8`), starts the app when it finishes, and its uninstaller removes
  the Claude Code hooks (`SQRM8.exe hooks uninstall`).

Quick check of any build: `<binary> status` must print the daemon/device report, and
`echo '{}' | <binary> hook` must exit 0 instantly.

## CI

- `.github/workflows/ci.yml` (every push and PR): unit tests on Ubuntu, macOS and Windows (Python 3.12), a
  PyInstaller smoke build on each (runs `status` and `hook` with the frozen binary), and both firmware builds
  (`pio run -e companion`).
- `.github/workflows/release.yml` (tags `v*`, or run by hand from the Actions tab): builds the firmware bundle,
  the app for Windows x64, macOS arm64, macOS x64 and Linux x64 with that firmware inside, the installers, and
  publishes a GitHub Release with auto-generated notes. Run by hand on a branch, it only uploads the artifacts.

## Cut a release

1. Bump `host/companion/version.py` (`__version__`, the app version).
2. If the firmware changed since the last release, bump `FW_VERSION` in `firmware/src/core/version.h`: that is
   how installed apps know to offer a firmware update.
3. Commit, then tag and push:
   ```bash
   git tag v0.8.0 && git push origin main v0.8.0
   ```
   The tag must be exactly `v` + `__version__`; the release workflow checks it (`packaging/check_version.py`)
   and fails otherwise.
4. Wait for the `release` workflow; the release appears on the repo's Releases page with the installers and the
   firmware zips attached. Edit the notes if needed.

## Unsigned builds

The builds are not code-signed or notarized, so the OSes warn the first time:

- **macOS** (Gatekeeper: "cannot be opened because the developer cannot be verified" or "is damaged"): drag the
  app to Applications, then **right-click (or Control-click) it → Open → Open**. On macOS 15+, if there is no
  Open button: try to open it once, then System Settings → Privacy & Security → **Open Anyway**. From a terminal:
  `xattr -dr com.apple.quarantine /Applications/SQRM8.app`.
- **Windows** (SmartScreen: "Windows protected your PC"): click **More info → Run anyway**. Some antivirus tools
  flag unsigned PyInstaller apps; the source and the build logs are public in the repo's Actions tab.
- **Linux**: `chmod +x SQRM8-*.AppImage` and run it. The AppImage needs FUSE 2 (`libfuse2` /
  `fuse2` package); without it, run it with `--appimage-extract-and-run`, or use the `.tar.gz` instead.

## Upgrading from "Claudius Maximus" (up to 0.7.x)

The app was renamed SQRM8 in 0.8.0, and every installed name changed with it. Apps up to 0.7.x look for
`ClaudiusMaximus-*` assets, so they cannot update themselves to 0.8.0: their update reports that the release has
no download for this computer and names the Releases page, where the user gets the SQRM8 installer once.

- **Windows**: the SQRM8 installer (a new AppId) finds the old install by the old AppId, stops
  `ClaudiusMaximus.exe`, deletes its folder, `Run` value, shortcuts and Apps & features entry. It does not run the
  old uninstaller, which would strip the Claude Code hooks: the new app re-points them to itself on its first
  start and moves `~/.claudius-maximus` to `~/.sqrm8`.
- **macOS / Linux**: `SQRM8.app` / the new AppImage sit next to the old app, which the user deletes; the new app
  takes over the hooks, the start-at-login entry and the settings folder on its first start.
- **Source checkouts**: `tools/install.sh` stops and removes the old `com.claudius-maximus.daemon` LaunchAgent or
  `claudius-maximus.service` before installing `com.sqrm8.daemon` / `sqrm8.service`, and prints how to swap an
  old `/etc/udev/rules.d/99-claudius-maximus.rules` (needs root); `tools/uninstall.sh` removes both names.
