# TulipWars 2026

TulipWars 2026 is an anonymous BBS-style space game for Tulip. Explore star systems, trade commodities, scan deep-space signals, fight alien ships, meet other anonymous captains at stations, and create procedural music from an Element115 ship tracker.

## Current release

**v0.1.7 — Tulip Web public test**

The Web build is being tested before installation on physical Tulip CC hardware is recommended.

## Features

- Anonymous persistent captain and ship identity
- No account, password, email, OAuth, cookies, or login API
- Nine explorable star systems
- Fuel-based travel and random space encounters
- Dynamic station commodity markets
- Cargo, credits, hull, shields, fuel, salvage, and rewards
- Turn-based alien combat
- Anonymous station-local BBS chat and docked-player presence
- 100% AMY-synthesized audio with no samples
- Randomized Juno-style procedural space ambience
- Element115 Tracker with an 8×16 sequencer
- AMY playback, optional MIDI output, and Standard MIDI File export
- Read-only Tulip World lounge
- No automatic Tulip World posts or gameplay spam

## Quick Tulip Web installation

1. Download `INSTALL_TULIPWARS_WEB_v0.1.7.py`.
2. Open `https://tulip.computer/run/`.
3. Click **Show code editor**.
4. Upload the installer with the blue Upload button.
5. Select it and click the red load-to-editor arrow.
6. Click the green Run button.

The installer contains the complete game. No terminal typing, clipboard paste, TAR extraction, account, or login is required.

## Repository layout

- `INSTALL_TULIPWARS_WEB_v0.1.7.py` — complete one-file Web installer
- `tulipwars2026/` — readable Tulip/MicroPython game source
- `website/` — PHP 8.4-compatible anonymous universe relay and dashboard
- `docs/` — features, controls, installation, and testing information
- `release-assets/` — complete and Discord-ready release archives

## Server privacy

The public source package intentionally excludes runtime universe state:

- `website/data/state.json`
- Tulip `local_state.json`
- exported `ELEMENT115_*.mid` files

TulipWars never calls `world.post_message()` and never automatically publishes gameplay events to Tulip World.
