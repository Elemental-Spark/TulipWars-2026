<?php
declare(strict_types=1);
require __DIR__ . '/config.php';
$state = ['players'=>[], 'chat'=>[], 'total_actions'=>0];
if (is_file(TULIPWARS_STATE_FILE)) {
    $decoded = json_decode((string)file_get_contents(TULIPWARS_STATE_FILE), true);
    if (is_array($decoded)) $state = array_merge($state, $decoded);
}
$now = time();
$online = array_filter($state['players'], fn($player)=>($player['last_seen'] ?? 0) >= $now - TULIPWARS_ONLINE_SECONDS);
function h(string $value): string { return htmlspecialchars($value, ENT_QUOTES, 'UTF-8'); }
?><!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>TulipWars 2026 v0.1.6</title>
<link rel="stylesheet" href="style.css">
</head>
<body>
<main>
<header>
<p class="signal">ELEMENTAL SPARK ANONYMOUS SIGNAL NETWORK</p>
<h1>TulipWars 2026</h1>
<p class="version">FULL BUILD v<?=h(TULIPWARS_VERSION)?></p>
<p>A tiny anonymous space BBS for Tulip CC, powered by PHP and AMY.</p>
</header>
<section class="stats">
<div><strong><?=count($online)?></strong><span>signals online</span></div>
<div><strong><?=count($state['players'])?></strong><span>anonymous ships</span></div>
<div><strong><?=(int)$state['total_actions']?></strong><span>universe actions</span></div>
</section>
<section>
<h2>Download</h2>
<p><a class="button" download href="downloads/INSTALL_TULIPWARS_WEB_v0.1.6.py">Download the complete one-file Tulip installer</a></p>
<p class="muted">The installer contains the whole game. It does not fetch a TAR, call a per-file endpoint, upload to Tulip World, or scatter repair scripts.</p>
<p class="muted">There are no accounts, login API, cookies, email addresses, or automatic Tulip World posts.</p>
</section>
<section>
<h2>Active anonymous ships</h2>
<table><thead><tr><th>Callsign</th><th>System</th><th>Activity</th></tr></thead><tbody>
<?php if (!$online): ?><tr><td colspan="3">No current signals.</td></tr><?php endif; ?>
<?php foreach ($online as $player): ?>
<tr><td><?=h((string)($player['callsign'] ?? 'ANON'))?></td><td><?=h((string)($player['system'] ?? 'UNKNOWN'))?></td><td><?=h((string)($player['activity'] ?? 'DOCKED'))?></td></tr>
<?php endforeach; ?>
</tbody></table>
</section>
<section>
<h2>How the relay works</h2>
<p>Each Tulip creates a random local ship ID. The ID identifies saved cargo and ship state, but it is not a login and is not connected to personal information. Station messages stay on this website. Tulip World is never used by the installer or game for uploads. Public chat remains a separate user-chosen action in the official worldui app.</p>
<p><a href="api.php">API health report</a></p>
</section>
</main>
</body>
</html>
