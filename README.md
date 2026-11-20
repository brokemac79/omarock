# OmaRock

An independent Roborock companion for Omarchy: a theme-aware native bar widget plus a loopback-only map and control dashboard. **Early alpha, not affiliated with Roborock.** MIT licensed. Private development repository for now.

## Features

- Robot-reported status, battery and dock tank flags (not water levels).
- Saved floors and room names, current floor map and cleaning route.
- Rooms / whole-floor / rectangular-zone planning, cleaning mode and passes.
- Native Omarchy bar entry opens a responsive dashboard.
- Cleaning history with honest unknown-room labels and maintenance hours.
- Control is locked by default; explicit configuration and per-action confirmation are required.

## Install on Omarchy

Requires Python 3.12+, uv and Omarchy 4's Quickshell plugin host.

```sh
omarchy plugin add https://github.com/brokemac79/omarock.git
cd ~/.config/omarchy/plugins/io.github.brokemac79.omarock
uv venv --python 3.12
uv pip install --python .venv/bin/python 'python-roborock[cli]==7.23.2'
.venv/bin/roborock login --email YOUR_EMAIL
omarchy plugin enable io.github.brokemac79.omarock
```

Private repo access requires GitHub authentication. Sign in via email code in your own terminal. Tokens are stored by the library in `~/.roborock`, never in this repo. Select `device_id` in private `~/.config/omarock/config.json` only if multiple robots are present.

Click the bar widget to open. Demo: `.venv/bin/python omarock.py open --demo` (if a live server is already running, stop it first). The backend runs only while its process is running; it is not installed as a system service. No history monitoring while the computer is off.

## Safety / commissioning

Until physically supervised Saros 20 testing, keep control disabled. To commission, create `~/.config/omarock/config.json` with `{"allow_control": true}`, mode 0600, then restart the backend. Requests require bearer authentication, same-origin POST, selected-floor confirmation, valid room IDs, battery >=20%, no reported error, and an idle robot. The plugin never switches floor maps automatically. Move the robot and select its floor using the official app before using another floor.

Mode setting and starting are two separate API operations: failure between them may leave settings changed. A timeout is **uncertain**, not proof nothing happened; check the official app before retrying. Submitted requests are not completed cleans. Whole-floor repeat passes are not implemented; select rooms for repeats. Zone calibration is mathematically mapped from parsed map calibration but physically unverified.

## Security

Server binds 127.0.0.1:18776 only. Per-run bearer token goes in the initial URL fragment, then browser sessionStorage. Private runtime files are under `~/.local/state/omarock` (0700). No CORS, strict Host/Origin checks and restrictive CSP. Do not expose the port or put tokens in screenshots/issues. Other applications running as your user can read your files; this is not a sandbox. Browser access is trusted local-user access. Do not run untrusted plugins.

The UI makes no secret/API requests to external websites. Device/library traffic may use Roborock cloud. Map images are private home data; runtime state is gitignored and outside the checkout. No analytics.

## Verification status

- Saros 20 status, maps, room names, raw cleaning records and consumables were verified from a VPS integration before this project.
- Clean tank removal/replacement flips its flag. Dirty tank removal is not physically verified.
- Project-specific live backend, desktop rendering and tests: see `docs/VERIFICATION.md`.
- No cleaning, map editing, dock cycles or robot settings changes were performed during development.
- Existing historical records can omit room IDs. No invented per-room freshness or reconstruction from unavailable historical paths.

## Development

```sh
python3 -m unittest discover -s tests -v
node --check web/app.js
omarchy plugin validate .
```

No production mock data fallback: demo mode is explicitly marked and commands are rejected. v0.1 uses a polling backend; live snapshots refresh roughly every minute plus device-request latency. The UI labels stale data.

## Credits

Connectivity and parsing: [python-roborock](https://github.com/Python-roborock/python-roborock) (its own license). Design research: [roborock-web](https://github.com/sakerrr/roborock-web) and [saros-dashboard](https://github.com/datori/saros-dashboard). No source copied from those dashboards. Omarchy UI contracts and installed plugin patterns informed the bar integration. Own MIT license does not replace dependency licenses.
