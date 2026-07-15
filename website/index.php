<?php
declare(strict_types=1);
require __DIR__ . '/config.php';
$state = ['players'=>[], 'chat'=>[], 'total_actions'=>0, 'updated_at'=>0];
if (is_file(TULIPWARS_STATE_FILE)) {
    $decoded = json_decode((string)file_get_contents(TULIPWARS_STATE_FILE), true);
    if (is_array($decoded)) $state = array_merge($state, $decoded);
}
if (!is_array($state['players'])) $state['players'] = [];
$now = time();
$online = array_filter($state['players'], fn($player)=>is_array($player) && (int)($player['last_seen'] ?? 0) >= $now - TULIPWARS_ONLINE_SECONDS);
$systemsOnline = [];
foreach ($online as $player) {
    $system = (string)($player['system'] ?? 'UNKNOWN');
    $systemsOnline[$system] = ($systemsOnline[$system] ?? 0) + 1;
}
function h(string $value): string { return htmlspecialchars($value, ENT_QUOTES, 'UTF-8'); }
?><!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="TulipWars 2026 is an anonymous BBS-style space trading, exploration, combat, chat, and AMY music game for Tulip.">
<title>TulipWars 2026 v<?=h(TULIPWARS_VERSION)?></title>
<link rel="stylesheet" href="style.css?v=017">
</head>
<body>
<main>
<header class="hero">
<p class="signal">ELEMENTAL SPARK // ANONYMOUS SIGNAL NETWORK</p>
<h1>TulipWars <span>2026</span></h1>
<p class="version">FULL WEB BUILD v<?=h(TULIPWARS_VERSION)?></p>
<p class="lead">Explore the stars, trade between stations, fight alien signals, talk with other anonymous captains, and compose procedurally generated AMY music from your ship console.</p>
<div class="actions">
<a class="button primary" download href="downloads/INSTALL_TULIPWARS_WEB_v0.1.7.py">Download the complete v0.1.7 installer</a>
<a class="button" href="api.php">View API health</a>
</div>
</header>

<section class="stats" aria-label="Universe statistics">
<div><strong><?=count($online)?></strong><span>signals online</span></div>
<div><strong><?=count($state['players'])?></strong><span>anonymous ships</span></div>
<div><strong><?=(int)$state['total_actions']?></strong><span>universe actions</span></div>
<div><strong>9</strong><span>star systems</span></div>
</section>

<section class="panel two-column">
<div>
<h2>Install on Tulip Web</h2>
<ol>
<li>Open <strong>tulip.computer/run</strong>.</li>
<li>Click <strong>Show code editor</strong>.</li>
<li>Upload <code>INSTALL_TULIPWARS_WEB_v0.1.7.py</code>.</li>
<li>Select it, load it, and click the green Run button.</li>
</ol>
<p class="muted">The single Python file contains the complete game. No terminal typing, TAR extraction, login, password, or clipboard paste is required.</p>
</div>
<div>
<h2>Current build</h2>
<ul class="checklist">
<li>Anonymous persistent ship identity</li>
<li>Space travel, trading, scans, and alien combat</li>
<li>Station-local BBS chat and online presence</li>
<li>AMY-only effects and randomized Juno ambience</li>
<li>Element115 Tracker with MIDI export</li>
<li>Read-only Tulip World access—no automatic posts</li>
</ul>
</div>
</section>

<section class="panel">
<h2>Active anonymous ships</h2>
<div class="table-wrap"><table><thead><tr><th>Callsign</th><th>System</th><th>Activity</th><th>Client</th></tr></thead><tbody>
<?php if (!$online): ?><tr><td colspan="4">No current signals. The relay is standing by.</td></tr><?php endif; ?>
<?php foreach ($online as $player): ?>
<tr>
<td><?=h((string)($player['callsign'] ?? 'ANON'))?></td>
<td><?=h((string)($player['system'] ?? 'UNKNOWN'))?></td>
<td><?=h((string)($player['activity'] ?? 'DOCKED'))?></td>
<td><?=h((string)($player['client_version'] ?? ''))?></td>
</tr>
<?php endforeach; ?>
</tbody></table></div>
</section>

<section class="panel two-column">
<div>
<h2>Anonymous by design</h2>
<p>Each installation creates a random local ship ID. It saves cargo and ship progress but is not an account and is never connected to a password, email address, OAuth identity, profile, or login API.</p>
</div>
<div>
<h2>Respectful Tulip World use</h2>
<p>Gameplay, station boards, and presence stay on this self-hosted relay. TulipWars does not upload packages, announcements, chat, or gameplay events to Tulip World. The in-game lounge is read-only.</p>
</div>
</section>

<footer>
<p>TulipWars 2026 v<?=h(TULIPWARS_VERSION)?> // API <?=h(TULIPWARS_API_REVISION)?></p>
</footer>
</main>
</body>
</html>
