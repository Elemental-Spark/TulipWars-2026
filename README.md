# TulipWars 2026

TulipWars 2026 is an anonymous BBS-style space game for Tulip Web, Desktop, and physical Tulip CC hardware. Explore star systems, trade commodities, scan deep-space signals, fight alien ships, meet anonymous captains at stations, and compose procedural music from an Element115 ship tracker.

## Current release

**v0.1.8 — Hardware Audio + MIDI Download Update**

## v0.1.8 highlights

- Maximum six managed Juno voices throughout the game
- Procedural ambience uses four Juno voices and does not overlap chords
- Opening Element115 Tracker fully releases the background synth
- Dense eight-row tracker patterns emit at most six simultaneous notes
- Leaving Tracker releases its synth before ambience is restored
- Tulip Web exports trigger a real browser `.mid` download
- Physical Tulip/Desktop exports remain stored locally

## Core features

- Anonymous persistent captain and ship identity
- No accounts, passwords, email, OAuth, cookies, or login API
- Nine explorable star systems
- Travel, fuel, scans, salvage, alien encounters, and turn-based combat
- Dynamic station commodity markets
- Anonymous station-local BBS chat and docked-player presence
- AMY-only procedural ambience and sound effects
- Element115 8x16 tracker with MIDI output and Standard MIDI File export
- Read-only Tulip World lounge with no automatic posts

## Install or update

1. Download `INSTALL_OR_UPDATE_TULIPWARS_v0.1.8.py`.
2. Open `https://tulip.computer/run/`.
3. Click **Show code editor**.
4. Upload the installer, select it, and load it.
5. Click the green **Run** button.

The one-file updater preserves `local_state.json`, every `ELEMENT115_*.mid` file, and an existing custom relay configuration.

## Repository layout

- `INSTALL_OR_UPDATE_TULIPWARS_v0.1.8.py` — complete one-file installer/updater
- `tulipwars2026/` — readable Tulip/MicroPython source
- `website/` — PHP anonymous universe API and dashboard
- `docs/` — installation, controls, changes, and test notes
- `release-assets/` — full, public-update, and website-sync archives

## Privacy

Runtime state is deliberately excluded from GitHub: `website/data/state.json`, `local_state.json`, and exported `ELEMENT115_*.mid` files are never committed. TulipWars never calls `world.post_message()` and never automatically publishes gameplay or files to Tulip World.
