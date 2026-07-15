# TulipWars 2026

TulipWars 2026 is an anonymous BBS-style space game for Tulip Web, Tulip Desktop, and Tulip CC hardware. Explore nine star systems, trade commodities, scan deep space, fight alien signals, meet anonymous captains at stations, and create procedural music from the Element115 Tracker.

## Current release

**v0.1.7 — confirmed working Tulip Web baseline**

The readable game source, complete one-file installer, PHP 8.4 website/API, documentation, and release archives are included here.

## Features

- Anonymous persistent ship identity with no accounts or login API
- Nine systems, fuel-based travel, random events, and dynamic markets
- Cargo, credits, hull, shields, scans, salvage, and alien combat
- Anonymous station-local BBS chat and online presence
- 100% AMY-synthesized effects and randomized Juno ambience
- Element115 Tracker with AMY playback and Standard MIDI File export
- Read-only Tulip World lounge
- No automatic Tulip World messages, uploads, or gameplay spam

## Tulip Web installation

1. Download `INSTALL_TULIPWARS_WEB_v0.1.7.py`.
2. Open `https://tulip.computer/run/`.
3. Show the code editor and upload the installer.
4. Load it and click the green Run button.

## Self-hosted website/API

Upload the contents of `website/` to `/tulipwars2026/` on a PHP 8.4-compatible host. Preserve the live `website/data/state.json`; it is excluded from this repository and all release packages.

The API remains intentionally anonymous and flat-file based. It does not use passwords, email, OAuth, cookies, account profiles, or a login API.
