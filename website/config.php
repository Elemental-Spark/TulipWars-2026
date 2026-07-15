<?php
declare(strict_types=1);

const TULIPWARS_VERSION = '0.1.7';
const TULIPWARS_STATE_FILE = __DIR__ . '/data/state.json';
const TULIPWARS_CHAT_LIMIT = 100;
const TULIPWARS_ONLINE_SECONDS = 120;

// Flat-file mode is intentional: no database, account system, login API,
// email collection, OAuth, cookies, or personal profile is required.
