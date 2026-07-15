<?php
declare(strict_types=1);

const TULIPWARS_VERSION = '0.1.10';
const TULIPWARS_API_REVISION = '2026-07-15-v0.1.10-installer-hardware-recovery';
const TULIPWARS_STATE_FILE = __DIR__ . '/data/state.json';
const TULIPWARS_CHAT_LIMIT = 100;
const TULIPWARS_ONLINE_SECONDS = 120;
const TULIPWARS_CARGO_CAPACITY = 60;

// TulipWars deliberately uses anonymous flat-file persistence. There is no
// account database, login API, password, email collection, OAuth, profile,
// authentication cookie, or automatic Tulip World posting.
