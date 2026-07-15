<?php
declare(strict_types=1);
require __DIR__ . '/config.php';

header('Content-Type: application/json; charset=utf-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Cache-Control: no-store');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

function respond(array $payload, int $status = 200): never {
    http_response_code($status);
    echo json_encode($payload, JSON_UNESCAPED_SLASHES | JSON_UNESCAPED_UNICODE);
    exit;
}

function systems(): array {
    return [
        ['id'=>'SOLACE',   'name'=>'Solace Station',   'type'=>'HUB',       'danger'=>1, 'x'=>0,  'y'=>0],
        ['id'=>'MOSS',     'name'=>'Mosswater Relay',  'type'=>'GARDEN',    'danger'=>1, 'x'=>3,  'y'=>2],
        ['id'=>'VEGA04',   'name'=>'Vega-04 Exchange', 'type'=>'TRADE',     'danger'=>2, 'x'=>7,  'y'=>1],
        ['id'=>'KHEPRI',   'name'=>'Khepri Outpost',   'type'=>'MINING',    'danger'=>3, 'x'=>9,  'y'=>6],
        ['id'=>'FAULT10',  'name'=>'Fault City GOTO10','type'=>'ANOMALY',   'danger'=>5, 'x'=>4,  'y'=>10],
        ['id'=>'CLEAN',    'name'=>'The Clean Machine','type'=>'CITYSHIP',  'danger'=>4, 'x'=>12, 'y'=>8],
        ['id'=>'SHEPHERD', 'name'=>'Shepherd Array',   'type'=>'SIGNAL',    'danger'=>5, 'x'=>15, 'y'=>2],
        ['id'=>'ELANOR',   'name'=>'Elanor Deep Field','type'=>'UNKNOWN',   'danger'=>5, 'x'=>18, 'y'=>11],
        ['id'=>'TULIP',    'name'=>'Tulip World Gate', 'type'=>'COMMUNITY', 'danger'=>2, 'x'=>2,  'y'=>7],
    ];
}

function commodities(): array {
    return [
        ['id'=>'water',    'name'=>'Clean Water',    'base'=>22],
        ['id'=>'food',     'name'=>'Garden Rations', 'base'=>31],
        ['id'=>'ore',      'name'=>'Element Ore',    'base'=>64],
        ['id'=>'circuits', 'name'=>'Tulip Circuits', 'base'=>95],
        ['id'=>'signals',  'name'=>'Lost Signals',   'base'=>145],
        ['id'=>'artifact', 'name'=>'Alien Artifact', 'base'=>260],
    ];
}

function system_by_id(string $id): ?array {
    foreach (systems() as $system) {
        if ($system['id'] === $id) return $system;
    }
    return null;
}

function commodity_by_id(string $id): ?array {
    foreach (commodities() as $commodity) {
        if ($commodity['id'] === $id) return $commodity;
    }
    return null;
}

function clean_id(mixed $value): string {
    $value = strtoupper((string)$value);
    $value = preg_replace('/[^A-Z0-9_-]/', '', $value) ?? '';
    return substr($value, 0, 48);
}

function clean_callsign(mixed $value): string {
    $value = strtoupper(trim((string)$value));
    $value = preg_replace('/[^A-Z0-9 _.-]/', '', $value) ?? 'ANON';
    $value = trim(substr($value, 0, 20));
    return $value !== '' ? $value : 'ANON';
}

function clean_message(mixed $value): string {
    $value = trim((string)$value);
    $value = preg_replace('/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u', '', $value) ?? '';
    return trim(substr($value, 0, 240));
}

function initial_state(): array {
    return [
        'version'=>TULIPWARS_VERSION,
        'created_at'=>time(),
        'players'=>[],
        'chat'=>[],
        'total_actions'=>0,
    ];
}

function mutate_state(callable $callback): array {
    $directory = dirname(TULIPWARS_STATE_FILE);
    if (!is_dir($directory) && !mkdir($directory, 0775, true) && !is_dir($directory)) {
        respond(['ok'=>false, 'error'=>'Could not create website/data'], 500);
    }
    $handle = fopen(TULIPWARS_STATE_FILE, 'c+');
    if ($handle === false) respond(['ok'=>false, 'error'=>'Could not open state file'], 500);
    if (!flock($handle, LOCK_EX)) {
        fclose($handle);
        respond(['ok'=>false, 'error'=>'Could not lock state file'], 503);
    }
    rewind($handle);
    $raw = stream_get_contents($handle);
    $state = is_string($raw) && trim($raw) !== '' ? json_decode($raw, true) : null;
    if (!is_array($state)) $state = initial_state();
    $result = $callback($state);
    $state['total_actions'] = (int)($state['total_actions'] ?? 0) + 1;
    rewind($handle);
    ftruncate($handle, 0);
    fwrite($handle, json_encode($state, JSON_PRETTY_PRINT | JSON_UNESCAPED_SLASHES));
    fflush($handle);
    flock($handle, LOCK_UN);
    fclose($handle);
    return $result;
}

function ensure_player(array &$state, string $deviceId, string $callsign): array {
    if (!isset($state['players'][$deviceId]) || !is_array($state['players'][$deviceId])) {
        $state['players'][$deviceId] = [
            'callsign'=>$callsign,
            'ship_name'=>'Lost Tulip ' . substr($deviceId, -4),
            'system'=>'SOLACE',
            'credits'=>1000,
            'fuel'=>100,
            'hull'=>100,
            'shield'=>100,
            'cargo'=>['water'=>3, 'food'=>3, 'ore'=>0, 'circuits'=>0, 'signals'=>0, 'artifact'=>0],
            'battle'=>null,
            'created_at'=>time(),
            'last_seen'=>time(),
            'activity'=>'DOCKED',
        ];
    }
    $state['players'][$deviceId]['callsign'] = $callsign;
    $state['players'][$deviceId]['last_seen'] = time();
    return $state['players'][$deviceId];
}

function public_player(array $player): array {
    $system = system_by_id((string)$player['system']);
    return [
        'callsign'=>$player['callsign'],
        'ship_name'=>$player['ship_name'],
        'system'=>$player['system'],
        'system_name'=>$system['name'] ?? $player['system'],
        'credits'=>(int)$player['credits'],
        'fuel'=>(int)$player['fuel'],
        'hull'=>(int)$player['hull'],
        'shield'=>(int)$player['shield'],
        'cargo'=>$player['cargo'],
    ];
}

function online_at(array $state, string $systemId, string $excludeId = ''): array {
    $online = [];
    $minimum = time() - TULIPWARS_ONLINE_SECONDS;
    foreach (($state['players'] ?? []) as $id=>$player) {
        if ($id === $excludeId) continue;
        if (($player['system'] ?? '') !== $systemId) continue;
        if ((int)($player['last_seen'] ?? 0) < $minimum) continue;
        $online[] = [
            'callsign'=>$player['callsign'] ?? 'ANON',
            'activity'=>$player['activity'] ?? 'DOCKED',
        ];
    }
    return array_slice($online, 0, 20);
}

function market_for(string $systemId): array {
    $period = intdiv(time(), 600);
    $items = [];
    foreach (commodities() as $commodity) {
        $hash = crc32($period . ':' . $systemId . ':' . $commodity['id']);
        $swing = (($hash % 41) - 20) / 100;
        $buy = max(2, (int)round($commodity['base'] * (1 + $swing)));
        $sell = max(1, (int)round($buy * 0.82));
        $items[] = ['id'=>$commodity['id'], 'name'=>$commodity['name'], 'buy'=>$buy, 'sell'=>$sell];
    }
    return ['period'=>$period, 'items'=>$items];
}

function packet(array $state, string $deviceId, string $message = ''): array {
    $player = $state['players'][$deviceId];
    return [
        'ok'=>true,
        'version'=>TULIPWARS_VERSION,
        'message'=>$message,
        'player'=>public_player($player),
        'universe'=>[
            'systems'=>systems(),
            'commodities'=>array_map(fn($item)=>['id'=>$item['id'], 'name'=>$item['name']], commodities()),
        ],
        'online'=>online_at($state, $player['system'], $deviceId),
        'battle'=>$player['battle'],
        'market'=>market_for($player['system']),
    ];
}

function apply_damage(array &$player, int $damage): int {
    $remaining = $damage;
    if ($player['shield'] > 0) {
        $absorbed = min($player['shield'], $remaining);
        $player['shield'] -= $absorbed;
        $remaining -= $absorbed;
    }
    if ($remaining > 0) $player['hull'] = max(0, $player['hull'] - $remaining);
    return $damage;
}

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    respond([
        'ok'=>true,
        'game'=>'TulipWars 2026',
        'version'=>TULIPWARS_VERSION,
        'mode'=>'anonymous-flat-file',
        'login_api'=>false,
        'tulip_world_auto_posts'=>false,
    ]);
}

$raw = file_get_contents('php://input');
$input = json_decode(is_string($raw) ? $raw : '', true);
if (!is_array($input)) $input = $_POST;
$action = strtolower((string)($input['action'] ?? ''));
$deviceId = clean_id($input['device_id'] ?? '');
$callsign = clean_callsign($input['callsign'] ?? 'ANON');

if ($deviceId === '' || strlen($deviceId) < 6) respond(['ok'=>false, 'error'=>'Anonymous device_id is required'], 400);

$result = mutate_state(function(array &$state) use ($action, $deviceId, $callsign, $input): array {
    ensure_player($state, $deviceId, $callsign);
    $player =& $state['players'][$deviceId];

    switch ($action) {
        case 'hello':
        case 'status':
            $player['activity'] = 'AT COMMAND DECK';
            return packet($state, $deviceId, 'ANONYMOUS SIGNAL LINK ESTABLISHED');

        case 'heartbeat':
            $player['activity'] = 'DOCKED';
            return packet($state, $deviceId, '');

        case 'market':
            $player['activity'] = 'TRADING';
            return packet($state, $deviceId, 'MARKET PRICES UPDATED');

        case 'trade':
            $commodityId = clean_id($input['commodity'] ?? '');
            $commodityId = strtolower($commodityId);
            $commodity = commodity_by_id($commodityId);
            if ($commodity === null) return ['ok'=>false, 'error'=>'Unknown commodity'];
            $side = strtolower((string)($input['side'] ?? ''));
            $quantity = max(1, min(20, (int)($input['quantity'] ?? 1)));
            $market = market_for($player['system']);
            $price = null;
            foreach ($market['items'] as $item) if ($item['id'] === $commodityId) $price = $item;
            if ($price === null) return ['ok'=>false, 'error'=>'No price available'];
            $held = (int)($player['cargo'][$commodityId] ?? 0);
            if ($side === 'buy') {
                $cost = $price['buy'] * $quantity;
                if ($player['credits'] < $cost) return ['ok'=>false, 'error'=>'Not enough credits'];
                if (array_sum($player['cargo']) + $quantity > 60) return ['ok'=>false, 'error'=>'Cargo hold is full'];
                $player['credits'] -= $cost;
                $player['cargo'][$commodityId] = $held + $quantity;
                $message = 'BOUGHT ' . $quantity . ' ' . strtoupper($commodityId);
            } elseif ($side === 'sell') {
                if ($held < $quantity) return ['ok'=>false, 'error'=>'Not enough cargo'];
                $player['cargo'][$commodityId] = $held - $quantity;
                $player['credits'] += $price['sell'] * $quantity;
                $message = 'SOLD ' . $quantity . ' ' . strtoupper($commodityId);
            } else {
                return ['ok'=>false, 'error'=>'Trade side must be buy or sell'];
            }
            $player['activity'] = 'TRADING';
            return packet($state, $deviceId, $message);

        case 'travel':
            $destinationId = clean_id($input['destination'] ?? '');
            $from = system_by_id($player['system']);
            $to = system_by_id($destinationId);
            if ($from === null || $to === null) return ['ok'=>false, 'error'=>'Unknown destination'];
            if ($from['id'] === $to['id']) return ['ok'=>false, 'error'=>'Already in that system'];
            $distance = sqrt((($to['x']-$from['x']) ** 2) + (($to['y']-$from['y']) ** 2));
            $fuelCost = max(4, (int)ceil($distance * 2.2));
            if ($player['fuel'] < $fuelCost) return ['ok'=>false, 'error'=>'Not enough fuel for that jump'];
            $player['fuel'] -= $fuelCost;
            $player['system'] = $to['id'];
            $player['shield'] = min(100, $player['shield'] + 5);
            $player['activity'] = 'ARRIVING FROM WARP';
            $roll = random_int(1, 100);
            $event = ['title'=>'QUIET ARRIVAL', 'text'=>'Stars bend, then settle around the station.'];
            if ($roll <= 18) {
                $enemyHull = 55 + ($to['danger'] * 12);
                $player['battle'] = [
                    'active'=>true,
                    'enemy_name'=>['VOID MITE','ANOMALY SKIFF','SHEPHERD DRONE','GLASS RAIDER'][random_int(0,3)],
                    'enemy_hull'=>$enemyHull,
                    'enemy_max_hull'=>$enemyHull,
                    'log'=>'HOSTILE SIGNAL FOLLOWED YOU THROUGH WARP.',
                ];
                $event = ['title'=>'WARP AMBUSH', 'text'=>'An alien vessel tears through the closing corridor.'];
            } elseif ($roll <= 35) {
                $salvage = random_int(30, 110);
                $player['credits'] += $salvage;
                $event = ['title'=>'DRIFTING CACHE', 'text'=>'Recovered ' . $salvage . ' anonymous trade credits.'];
            }
            $response = packet($state, $deviceId, 'ARRIVED AT ' . strtoupper($to['name']) . ' // FUEL -' . $fuelCost);
            $response['event'] = $event;
            return $response;

        case 'scan':
            if (is_array($player['battle']) && ($player['battle']['active'] ?? false)) return ['ok'=>false, 'error'=>'Resolve the active battle first'];
            $player['activity'] = 'SCANNING DEEP SPACE';
            $danger = system_by_id($player['system'])['danger'] ?? 1;
            $roll = random_int(1, 100);
            if ($roll <= 28 + ($danger * 4)) {
                $enemyHull = random_int(45, 70) + ($danger * 10);
                $player['battle'] = [
                    'active'=>true,
                    'enemy_name'=>['VOID MITE','ANOMALY SKIFF','SHEPHERD DRONE','GLASS RAIDER','CLEAN MACHINE SENTINEL'][random_int(0,4)],
                    'enemy_hull'=>$enemyHull,
                    'enemy_max_hull'=>$enemyHull,
                    'log'=>'THE CONTACT REFUSES ALL HAILS.',
                ];
                $event = ['title'=>'HOSTILE SIGNAL', 'text'=>'Weapons signatures lock onto your hull.'];
                $message = 'ALIEN CONTACT DETECTED';
            } elseif ($roll <= 62) {
                $credits = random_int(35, 150);
                $player['credits'] += $credits;
                if (random_int(1,100) <= 25) $player['cargo']['signals']++;
                $event = ['title'=>'LOST TRANSMISSION', 'text'=>'Decoded salvage worth ' . $credits . ' credits.'];
                $message = 'SIGNAL RECOVERED';
            } elseif ($roll <= 78) {
                $fuel = random_int(4, 14);
                $player['fuel'] = min(100, $player['fuel'] + $fuel);
                $event = ['title'=>'FUEL BLOOM', 'text'=>'Collected ' . $fuel . ' units of charged nebula gas.'];
                $message = 'FUEL RECOVERED';
            } else {
                $event = ['title'=>'TWO VOICES', 'text'=>'A blue and gold harmony maps a door that is not yet open.'];
                $message = 'THE LOST SIGNALS HEARD YOU';
            }
            $response = packet($state, $deviceId, $message);
            $response['event'] = $event;
            return $response;

        case 'combat':
            if (!is_array($player['battle']) || !($player['battle']['active'] ?? false)) return ['ok'=>false, 'error'=>'No active battle'];
            $command = strtolower((string)($input['command'] ?? ''));
            $battle =& $player['battle'];
            $damageTaken = 0;
            if ($command === 'fire') {
                $damage = random_int(14, 31);
                $battle['enemy_hull'] = max(0, $battle['enemy_hull'] - $damage);
                $battle['log'] = 'PULSE CANNONS HIT FOR ' . $damage . '.';
                if ($battle['enemy_hull'] > 0) $damageTaken = apply_damage($player, random_int(7, 19));
            } elseif ($command === 'defend') {
                $gain = random_int(10, 21);
                $player['shield'] = min(100, $player['shield'] + $gain);
                $damageTaken = apply_damage($player, random_int(2, 9));
                $battle['log'] = 'SHIELDS RECHARGED +' . $gain . '.';
            } elseif ($command === 'retreat') {
                if (random_int(1,100) <= 68) {
                    $battle['active'] = false;
                    $battle['log'] = 'ESCAPE VECTOR ACCEPTED.';
                } else {
                    $damageTaken = apply_damage($player, random_int(8, 20));
                    $battle['log'] = 'RETREAT BLOCKED BY TRACTOR SIGNAL.';
                }
            } else {
                return ['ok'=>false, 'error'=>'Unknown combat command'];
            }
            $message = $battle['log'];
            if ($battle['enemy_hull'] <= 0 && $battle['active']) {
                $battle['active'] = false;
                $reward = random_int(140, 420);
                $player['credits'] += $reward;
                if (random_int(1,100) <= 35) $player['cargo']['artifact']++;
                $message = 'ALIEN DESTROYED // REWARD ' . $reward;
                $battle['log'] = $message;
            }
            if ($player['hull'] <= 0) {
                $loss = intdiv($player['credits'], 2);
                $player['credits'] -= $loss;
                $player['hull'] = 45;
                $player['shield'] = 15;
                $player['fuel'] = max(25, $player['fuel']);
                $player['system'] = 'SOLACE';
                $battle['active'] = false;
                $message = 'RESCUED AT SOLACE // LOST ' . $loss . ' CREDITS';
            }
            $player['activity'] = 'IN ALIEN COMBAT';
            $response = packet($state, $deviceId, $message);
            $response['damage_taken'] = $damageTaken;
            return $response;

        case 'chat_list':
            $player['activity'] = 'READING STATION BOARD';
            $messages = $state['chat'][$player['system']] ?? [];
            $response = packet($state, $deviceId, 'STATION BOARD UPDATED');
            $response['messages'] = array_slice($messages, -40);
            return $response;

        case 'chat_post':
            $message = clean_message($input['message'] ?? '');
            if ($message === '') return ['ok'=>false, 'error'=>'Message is empty'];
            $systemId = $player['system'];
            if (!isset($state['chat'][$systemId]) || !is_array($state['chat'][$systemId])) $state['chat'][$systemId] = [];
            $state['chat'][$systemId][] = ['callsign'=>$player['callsign'], 'message'=>$message, 'time'=>time()];
            $state['chat'][$systemId] = array_slice($state['chat'][$systemId], -TULIPWARS_CHAT_LIMIT);
            $player['activity'] = 'POSTING TO STATION BOARD';
            $response = packet($state, $deviceId, 'MESSAGE POSTED TO YOUR PRIVATE STATION BOARD');
            $response['messages'] = array_slice($state['chat'][$systemId], -40);
            return $response;

        default:
            return ['ok'=>false, 'error'=>'Unknown action'];
    }
});

respond($result, ($result['ok'] ?? false) ? 200 : 400);
