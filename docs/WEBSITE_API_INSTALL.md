# Website/API installation

```text
TULIPWARS 2026 v0.1.7 — COMPLETE WEBSITE/API SYNC
====================================================

THIS IS A FULL REPLACEMENT FOR THE PUBLIC WEBSITE AND API.
It is not a repair patch and it contains the confirmed-working v0.1.7 installer.

UPLOAD
------
Upload every file INSIDE:

  UPLOAD_OVER_EXISTING_TULIPWARS2026/

over your existing server directory:

  /tulipwars2026/

CRITICAL: PRESERVE LIVE UNIVERSE STATE
--------------------------------------
DO NOT DELETE:

  /tulipwars2026/data/state.json

This package deliberately does not contain state.json, so a normal overwrite
preserves all anonymous ships, cargo, credits, station chat, and action counts.
The upgraded API automatically migrates older state records to v0.1.7.

THE UPDATE REPLACES
-------------------
- api.php
- config.php
- index.php
- style.css
- .htaccess
- data/.htaccess
- downloads/.htaccess
- downloads/INSTALL_TULIPWARS_WEB_v0.1.7.py

OBSOLETE FILES
--------------
These old patch-era files are blocked by the new .htaccess and may be deleted
from the host when convenient:

  /tulipwars2026/download.php
  /tulipwars2026/tulipwars_files.php
  /tulipwars2026/downloads/tulipwars2026.tar

VERIFY AFTER UPLOAD
-------------------
Open:

  https://elementalspark.com/tulipwars2026/
  https://elementalspark.com/tulipwars2026/api.php

The API health response must report version 0.1.7 and:

  "login_api": false
  "tulip_world_auto_posts": false

The dashboard download button must offer:

  INSTALL_TULIPWARS_WEB_v0.1.7.py

```
