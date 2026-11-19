# Customizing SQRM8

The firmware, the daemon and the hardware are meant to be adapted, and the fastest way is to open this repo in
Claude Code and ask: `CLAUDE.md` is the map an agent reads first, each subsystem has its own doc, and the tools
in `tools/dev.py` build, flash, screenshot and profile the device from the command line. Tell it what you want
and let it read the docs; the agent follows the same rules a contributor does (measure before and after, keep
the rendering on the main task, big buffers in PSRAM).

| You want | Where it lives | Ask for |
|---|---|---|
| Your own board or panel | `firmware/src/core/board.h` (pin map, expander or direct GPIO), `hal.cpp`, `st7701_init.h` | "add a board profile for my PCB: these GPIOs, no expander, shared reset" |
| Other colours, fonts, status mapping | `firmware/src/ui/theme.h`, `docs/TEAM.md` "Visual language" | "make the accent teal and the waiting state blue" |
| New or different screens | `firmware/src/screens/`, one file per screen, `PROTOCOL.md` for the data | "add a screen that shows X from the daemon" |
| M8's Studio art and animations (M8 is an original character; its sheets are the masters) | `firmware/assets/sprites/` (indexed PNGs, `tools/sprites/README.md`), `tools/room_sim.py` to preview on the host | "give Clawd a hat on Fridays" |
| What the daemon sends, how often | `host/companion/`, `docs/DESKTOP.md`, `PROTOCOL.md` | "send the git branch of each session too" |
| Screensaver, alerts | `firmware/src/fx/` | "a different screensaver after 10 minutes" |
| Another orientation or a USB port | `HAL_ROT180` build flag, `board.h` | "rotate the UI 90 degrees" |

Workflow: `DEV_NAME=<you> host/.venv/bin/python tools/dev.py build | flash | shot out.png --screen home` (see
`docs/DEVELOPMENT.md`); run the host tests with `HOME` pointing at an empty directory; for anything touching
rendering or the link, record a before/after with the probe in `docs/PERF.md`.

Hardware: `hardware/` holds the KiCad project and the panel reference. A board with the same pin map runs the
stock firmware; a different pin map is a new `board.h` profile.
