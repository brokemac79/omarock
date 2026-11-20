# OmaRock

**A native Roborock plugin for Omarchy.** The bar widget and application launcher open a separate, resizable, theme-aware native QML app window hosted by Omarchy’s Quickshell process. **No browser, WebView or web server.** Independent community project, not affiliated with Roborock. MIT licensed; private early-alpha development.

## Features

- Native bar status and a keyboard-accessible native app with Overview / History / Maintenance / Connection.
- Three-floor browsing, named room selection, current floor map and robot-reported cleaning route.
- Rooms / whole-floor / rectangular-zone cleaning plans; vacuum, mop or both; repeat passes for rooms/zones.
- Battery, washing/drying flags, clean/dirty tank flags (not fill levels), consumable hours and recent runs.
- Explicit read-only safety lock by default. Confirmation and physical-floor guard before any action.
- Snapshot timestamps and stale-state warnings. Unknown room history remains unknown.

## Install

Requires Omarchy 4 / Quickshell, uv and Python 3.12+.

```sh
omarchy plugin add https://github.com/brokemac79/omarock.git
uv venv --python 3.12 ~/.local/share/omarock/venv
uv pip install --python ~/.local/share/omarock/venv/bin/python 'python-roborock[cli]==7.23.2'
omarchy plugin enable io.github.brokemac79.omarock
cp ~/.config/omarchy/plugins/io.github.brokemac79.omarock/omarock.desktop ~/.local/share/applications/
```

Private repo access needs GitHub authentication. Click the robot bar icon or launch **OmaRock** from the application launcher to open the app window. Middle-click or press R in the panel to refresh; Escape closes the review or app window. The Python environment MUST live outside the plugin tree (Omarchy disallows internal symlinks). No auto-start daemon or listening port is installed.

## Account and private data

**Sign in inside the app:** open OmaRock → Connection, enter your Roborock account email, click **Send email code**, then enter the six-digit code and click **Sign in**. The app refreshes automatically. No terminal or password needed. Cancel or close the window to cancel an unfinished sign-in. Codes are passed over a private stdin pipe, kept only in memory, never logged, stored or put in command-line arguments. Request errors, invalid codes and expiry are shown in the form. Successful credentials replace the vendor cache atomically with mode 0600; an unsuccessful attempt preserves any existing session.

Email-code login uses the vendor library’s credential cache in `~/.roborock`. Never put credentials in the repository or issues. If several devices exist, set `device_id` in private `~/.config/omarock/config.json` (0600). Private snapshots and maps are under `~/.local/state/omarock/` (0700). Robot traffic may use Roborock’s cloud; the native interface itself has no web service or analytics.

## Safety / commissioning

Live Saros 20 actuation is **not physically verified**. Leave the default lock on until a supervised test. To explicitly commission, set `{"allow_control": true}` in the private config above and refresh the panel. The default is false. No configuration file or token is shipped in the repo.

Cleaning requires confirming the robot’s physical floor, valid current map and room IDs, battery >=20%, no reported errors and no active cleaning/returning task. The plugin does not switch maps automatically. Move the robot and select its floor using the official app first. Whole-floor repeats are not implemented; select rooms for repeats.

A request is **submitted**, never assumed complete. Mode setting and starting are separate API operations: failure in between may leave settings changed. Timeouts are uncertain; check the official app before retrying. Zone coordinate transformation uses the parsed map’s three-point calibration but needs a physical supervised test. Pause/dock are also gated until commissioning.

## Honest limitations

Only the active floor’s image is available; other saved floor names/rooms can be browsed without pretending their image is current. History may omit room IDs. No fabricated last-cleaned room dates or freshness layer. Maps use real robot-rendered data, not the illustrative furniture from the design concept. The app launcher and bar open/focus the same independent native window. It remains open when it loses focus and can be tiled or moved to another workspace. Narrow compositor-forced tiles scroll horizontally instead of overlapping controls. No browser or WebView.

## Development

```sh
python3 -m unittest discover -s tests -v
python3 -m py_compile omarock.py
omarchy plugin validate .
```

Read-only helper: `~/.local/share/omarock/venv/bin/python omarock.py snapshot`. The pure-stdlib `cached` command reads private state without connecting. All device code uses python-roborock 7.23.2.

## Credits and licensing

Connectivity and parsing: [python-roborock](https://github.com/Python-roborock/python-roborock), under its own license. Design research: [roborock-web](https://github.com/sakerrr/roborock-web) and [saros-dashboard](https://github.com/datori/saros-dashboard). No dashboard source copied. Native UI uses Omarchy’s existing `Ui.BarWidget`, `Ui.Panel` and `Ui.KeyboardPanel` contracts. MIT license covers this project, not third-party dependencies. See `docs/VERIFICATION.md` for exact evidence and outstanding tests.

### Cleaning rhythm (Timeline)
Native floor-grouped timeline: whole-floor rows plus each room, with independent
vacuum and mop lanes. Filter by floor; Edit saves a local repeat interval (Off or
1/2/3/7/14/30 days). Dates are anchored when the plan is saved. A due marker is a
plan, **not evidence of completed cleaning**. Plans do not automatically dispatch
or create Roborock timers. `Clean now` opens the Overview selection for review;
it never bypasses the active-floor/physical-floor checks or control lock.

Imported history currently lacks trustworthy room-and-cleaning-mode attribution;
last-clean dates therefore remain unknown. Existing floor activity remains under
History. A future scheduler needs explicit commissioning, sleep/offline recovery,
physical-floor availability and reliable completion tracking before automation
can be enabled. Local plans are private (`~/.local/state/omarock/plans.json`).
