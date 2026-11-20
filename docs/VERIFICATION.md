# Verification — 20 November 2026

The first browser-based implementation was rejected by Martin. It is superseded by a native QML plugin and attached Omarchy panel. No browser/server routes remain in the current implementation. Prior web UI checks do NOT count as native UI verification.

## Backend
- 18 validation/cached-state tests passed (room IDs, wrong floor, confirmation, mode, passes, zone bounds and missing calibration).
- Project helper connected read-only to real Saros 20 on VPS using existing login: battery/dock flags, three saved floors and room names, current map and three-point calibration, ten raw cleaning records, consumables. No warnings.
- Clean tank removal/replacement flags were physically tested earlier; dirty tank detection remains assumed, not physically tested.
- No cleaning, movement, map switching, settings writes or dock cycles during development.

## Desktop
- Surface Pro 3, Omarchy 4.5.0-3. Python 3.12 environment outside plugin folder.
- Native plugin schema validated. Actual native QML component compilation succeeded. After Omarchy shell restart, native summon returned ok; screenshots of overview (real cached map/battery/tank flags), keyboard-navigated History (real records) and Connection were visually inspected. No OmaRock QML runtime errors in final shell logs. Installed native desktop launcher opens via gtk-launch omarock. No listening port 18776 remains.
- Existing helper error-key collision fixed and regression tested: robot error=none is not interpreted as a failed helper command. Cached map margins cropped with matching calibration offsets; original timestamp retained.
- Desktop has no Roborock login yet. Cached snapshot copied privately from existing VPS read-only fetch, NOT a live desktop connection. No account tokens copied.

## Not verified
- Saros physical room/floor/zone cleaning, mode setting and pause/dock. Default lock remains on.
- Other-floor image retrieval; historical per-room coverage when room IDs are absent.
- Marketplace packaging/submission. Repository remains private.
