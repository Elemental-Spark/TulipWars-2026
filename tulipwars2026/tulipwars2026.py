import sys
import tulip

# Tulip temporarily adds a package folder to the module path while importing the
# main file. UIScreen activation happens later, after that temporary path may be
# gone. Keep the real package folder on sys.path before loading sibling modules.
tw_config = None
tw_storage = None
Client = None
AmbientEngine = None
Element115Tracker = None

APP = None
GAME = None
BOOT_ERROR = None


def _prepare_module_path(app=None):
    candidates = []
    if app is not None:
        try:
            candidates.append(app.app_dir)
        except Exception:
            pass
    try:
        filename = __file__
        if '/' in filename:
            candidates.append(filename.rsplit('/', 1)[0])
    except Exception:
        pass
    for path in candidates:
        if path and path not in sys.path:
            sys.path.insert(0, path)


def _load_modules(app=None):
    global tw_config, tw_storage, Client, AmbientEngine, Element115Tracker
    if tw_config is not None:
        return
    _prepare_module_path(app)
    import tw_config as loaded_config
    import tw_storage as loaded_storage
    from tw_net import Client as LoadedClient
    from tw_audio import AmbientEngine as LoadedAmbientEngine
    from tw_tracker import Element115Tracker as LoadedTracker
    tw_config = loaded_config
    tw_storage = loaded_storage
    Client = LoadedClient
    AmbientEngine = LoadedAmbientEngine
    Element115Tracker = LoadedTracker


class TulipWarsGame:
    WIDTH = 128
    HEIGHT = 50
    CONTENT_WIDTH = 95
    KEYPAD_X = 96
    TFB_CHAR_W = 8
    TFB_CHAR_H = 12
    FG = 159
    DIM = 67
    BRIGHT = 231
    ACCENT = 45
    ALERT = 196
    GOOD = 82
    BG = 0

    def __init__(self, app):
        self.app = app
        self.app_dir = getattr(app, "app_dir", ".")
        self.local = tw_storage.load(self.app_dir, tw_config.CALLSIGN_PREFIX)
        self.client = Client(
            tw_config.SERVER_URL,
            self.local["device_id"],
            self.local["callsign"],
            tw_config.GAME_VERSION,
        )
        self.audio = AmbientEngine()
        self.tracker = Element115Tracker(self.app_dir)
        self.screen = "home"
        self.data = {}
        self.online = False
        self.message = ""
        self.last_heartbeat = 0
        self.nav_systems = []
        self.market_items = []
        self.market_selected = 0
        self.chat_messages = []
        self.composing = False
        self.compose_text = ""
        self.world_messages = []
        self.last_tracker_redraw = 0
        self.request_pending = False
        self.heartbeat_pending = False
        self.touch_keys = []
        self.last_touch_ms = 0
        self.audio_fault = None

    def start(self):
        tulip.gpu_reset()
        tulip.tfb_start()
        tulip.tfb_font(0)
        tulip.bg_clear(self.BG)
        # Reactivating the app always returns to the command deck. This avoids
        # silently reallocating ambience behind a tracker screen after another
        # Tulip app temporarily deactivated TulipWars.
        if self.screen == "tracker":
            self.tracker.release()
            self.screen = "home"
        self.audio.start()
        if self.client.configured():
            self.connect()
        else:
            self.screen = "configure"
            self.draw()

    def stop(self):
        self.tracker.release()
        self.audio.stop()

    def _enter_tracker(self):
        # The Element115 console gets exclusive ownership of the managed Juno
        # pool. Merely opening the tracker unloads the ambient PatchSynth; it is
        # not left allocated silently while the grid is being edited.
        self.audio.suspend()
        self.tracker.release()
        self.screen = "tracker"
        self.message = "AMBIENT JUNO UNLOADED // TRACKER VOICE CAP: 6"

    def _leave_tracker(self):
        # Release all tracker voices first, then rebuild the procedural ambient
        # synth. Ambient notes do not begin until its delayed next chord.
        self.tracker.release()
        self.screen = "home"
        self.audio.resume()
        self.message = "TRACKER UNLOADED // PROCEDURAL AMBIENCE RESTORED"

    def connect(self):
        self.message = "CONTACTING ANONYMOUS RELAY..."
        self.draw()

        def connected(response):
            self.request_pending = False
            self._apply(response)
            self.online = True
            self.message = response.get("message", "ANONYMOUS RELAY CONNECTED")
            self.screen = "home"
            self.last_heartbeat = tulip.ticks_ms()
            self.draw()

        def failed(exc):
            self.request_pending = False
            self.online = False
            self.message = str(exc)
            self.screen = "offline"
            self.draw()

        self.request_pending = True
        self.client.hello(done=connected, fail=failed)

    def _apply(self, response):
        for key in ("player", "universe", "online", "battle", "market", "event"):
            if key in response:
                self.data[key] = response[key]
        if "messages" in response:
            self.chat_messages = response["messages"]
        if "message" in response:
            self.message = response["message"]
        systems = self.data.get("universe", {}).get("systems", [])
        self.nav_systems = systems[:9]
        self.market_items = self.data.get("market", {}).get("items", [])

    def _call(self, fn, *args, after=None):
        if self.client.async_mode and self.request_pending:
            self.message = "ANONYMOUS RELAY BUSY..."
            return None

        result = {"response": None}

        def succeeded(response):
            self.request_pending = False
            result["response"] = response
            self._apply(response)
            self.online = True
            self.audio.sfx("ok")
            if after is not None:
                after(response)
            if self.client.async_mode:
                self.draw()

        def failed(exc):
            self.request_pending = False
            self.online = False
            self.message = str(exc)
            self.audio.sfx("damage")
            if self.client.async_mode:
                self.draw()

        if self.client.async_mode:
            self.request_pending = True
        fn(*args, done=succeeded, fail=failed)
        return result["response"]

    def _blank(self):
        blank = " " * self.WIDTH
        for y in range(self.HEIGHT):
            tulip.tfb_str(0, y, blank, 0, self.FG, self.BG)

    def _line(self, y, text="", fg=None, bg=None, fmt=0):
        if y < 0 or y >= self.HEIGHT:
            return
        if fg is None:
            fg = self.FG
        if bg is None:
            bg = self.BG
        text = str(text).replace("\n", " ")
        if len(text) > self.CONTENT_WIDTH:
            text = text[:self.CONTENT_WIDTH]
        tulip.tfb_str(0, y, text + (" " * (self.CONTENT_WIDTH - len(text))), fmt, fg, bg)
        # Menu lines beginning with [X] can be touched directly as well as by
        # using the terminal keypad. This makes every numbered screen choice
        # accessible without a hardware keyboard.
        if len(text) >= 3 and text[0] == "[" and text[2] == "]":
            self.touch_keys.append((0, y, self.CONTENT_WIDTH - 1, y, ord(text[1])))

    def _pad_write(self, x, y, text, fg=None, bg=None, fmt=0):
        if y < 0 or y >= self.HEIGHT or x < 0 or x >= self.WIDTH:
            return
        if fg is None:
            fg = self.FG
        if bg is None:
            bg = self.BG
        text = str(text)[:self.WIDTH - x]
        tulip.tfb_str(x, y, text, fmt, fg, bg)

    def _touch_layout(self):
        if self.screen == "chat" and self.composing:
            return [
                (("1", 49), ("2", 50), ("3", 51), ("4", 52)),
                (("5", 53), ("6", 54), ("7", 55), ("8", 56)),
                (("9", 57), ("0", 48), ("A", 65), ("B", 66)),
                (("C", 67), ("D", 68), ("E", 69), ("F", 70)),
                (("G", 71), ("H", 72), ("I", 73), ("J", 74)),
                (("K", 75), ("L", 76), ("M", 77), ("N", 78)),
                (("O", 79), ("P", 80), ("Q", 81), ("R", 82)),
                (("S", 83), ("T", 84), ("U", 85), ("V", 86)),
                (("W", 87), ("X", 88), ("Y", 89), ("Z", 90)),
                (("SPC", 32), ("DEL", 8), ("ENT", 13), ("ESC", 27)),
            ]
        return [
            (("1", 49), ("2", 50), ("3", 51), ("R", 82)),
            (("4", 52), ("5", 53), ("6", 54), ("B", 66)),
            (("7", 55), ("8", 56), ("9", 57), ("S", 83)),
            (("0", 48), ("F", 70), ("D", 68), ("T", 84)),
            (("W", 87), ("P", 80), ("M", 77), ("E", 69)),
            (("[", 91), ("]", 93), ("-", 45), ("+", 43)),
            ((",", 44), (".", 46), ("SPC", 32), ("ENT", 13)),
            (("DEL", 8), ("ESC", 27), ("BACK", 48), ("REF", 82)),
        ]

    def _draw_touch_keypad(self):
        # The TFB default font is 8x12 on a 128x50 character grid. The keypad
        # therefore uses character-space hit boxes that map consistently to the
        # physical 1024x600 touch panel and to mouse clicks in Tulip Web.
        for row in range(self.HEIGHT):
            self._pad_write(self.KEYPAD_X - 1, row, "|", self.ACCENT)
        title = "TOUCH CHAT" if self.screen == "chat" and self.composing else "TOUCH TERMINAL"
        self._pad_write(self.KEYPAD_X + 8, 0, title[:16], self.BRIGHT, 17, 0x10)
        self._pad_write(self.KEYPAD_X, 1, "-" * 32, self.ACCENT)
        layout = self._touch_layout()
        start_y = 4 if len(layout) >= 10 else 6
        for row_index, row_keys in enumerate(layout):
            y = start_y + row_index * 4
            for col_index, item in enumerate(row_keys):
                label, code = item
                x = self.KEYPAD_X + col_index * 8
                shown = str(label)[:5].center(5)
                self._pad_write(x, y, "+-----+", self.DIM)
                self._pad_write(x, y + 1, "|" + shown + "|", self.BRIGHT, 17)
                self._pad_write(x, y + 2, "+-----+", self.DIM)
                self.touch_keys.append((x, y, x + 6, y + 2, code))
        self._pad_write(self.KEYPAD_X, 47, "TAP KEY OR MENU LINE".center(32), self.DIM)

    def touch(self, up):
        if not up:
            return
        try:
            now = tulip.ticks_ms()
        except Exception:
            now = 0
        if now and now - self.last_touch_ms < 140:
            return
        try:
            points = tulip.touch()
            px = int(points[0])
            py = int(points[1])
        except Exception:
            return
        if px < 0 or py < 0:
            return
        col = px // self.TFB_CHAR_W
        row = py // self.TFB_CHAR_H
        for x0, y0, x1, y1, code in reversed(self.touch_keys):
            if x0 <= col <= x1 and y0 <= row <= y1:
                self.last_touch_ms = now
                self.key(code)
                return

    def _header(self, section):
        self._line(0, "=" * self.WIDTH, self.ACCENT)
        title = " TULIPWARS 2026 // %s // ANONYMOUS SIGNAL %s " % (
            section,
            "ONLINE" if self.online else "OFFLINE",
        )
        self._line(1, title, self.BRIGHT, 17, 0x10)
        self._line(2, "=" * self.WIDTH, self.ACCENT)

    def _footer(self, help_text="[0] BACK"):
        self._line(46, "-" * self.WIDTH, self.DIM)
        self._line(47, help_text, self.BRIGHT)
        self._line(48, self.message, self.GOOD if self.online else self.ALERT)
        self._line(49, "CTRL-Q QUITS  //  CTRL-TAB SWITCHES APPS", self.DIM)

    def draw(self):
        self.touch_keys = []
        self._blank()
        method = getattr(self, "draw_" + self.screen, None)
        if method is None:
            self.screen = "home"
            method = self.draw_home
        method()
        self._draw_touch_keypad()

    def draw_configure(self):
        self._header("FIRST CONTACT")
        self._line(5, "THE SHIP CONSOLE NEEDS YOUR SELF-HOSTED PHP RELAY.", self.BRIGHT)
        self._line(7, "1. CTRL-TAB TO THE REPL, THEN cd('tulipwars2026')")
        self._line(8, "2. import tw_setup; tw_setup.configure()")
        self._line(9, "3. ENTER YOUR HTTPS .../api.php URL, RETURN TO /user, RUN AGAIN")
        self._line(12, "NO ACCOUNT, PASSWORD, EMAIL, OAUTH, OR LOGIN API IS USED.", self.GOOD)
        self._line(14, "A RANDOM LOCAL SHIP ID IS STORED ONLY IN local_state.json.")
        self._line(16, "CALLSIGN: %s" % self.local["callsign"], self.ACCENT)
        self._footer("EDIT CONFIG, THEN RESTART THE PACKAGE")

    def draw_offline(self):
        self._header("RELAY FAILURE")
        self._line(5, "THE SHIP CAN STILL RUN THE ELEMENT115 TRACKER OFFLINE.", self.BRIGHT)
        self._line(7, "[R] RETRY RELAY")
        self._line(8, "[6] OPEN ELEMENT115 TRACKER")
        self._line(10, "CHECK WI-FI, SERVER_URL, HTTPS, AND WEBSITE/data WRITE PERMISSION.")
        self._footer("[R] RETRY   [6] TRACKER")

    def draw_home(self):
        self._header("COMMAND DECK")
        player = self.data.get("player", {})
        system = player.get("system_name", "UNKNOWN")
        self._line(4, "CAPTAIN %-18s  SHIP %-20s" % (player.get("callsign", self.local["callsign"]), player.get("ship_name", "LOST TULIP")), self.BRIGHT)
        self._line(5, "LOCATION %-22s CREDITS %7s  FUEL %3s  HULL %3s  SHIELD %3s" % (
            system,
            player.get("credits", "-"),
            player.get("fuel", "-"),
            player.get("hull", "-"),
            player.get("shield", "-"),
        ))
        self._line(7, "[1] SHIP STATUS / CARGO")
        self._line(8, "[2] NAVIGATION / EXPLORE SPACE")
        self._line(9, "[3] STATION COMMODITY EXCHANGE")
        self._line(10, "[4] LONG-RANGE SCAN / ALIEN BATTLE")
        self._line(11, "[5] ANONYMOUS STATION CHAT")
        self._line(12, "[6] ELEMENT115 TRACKER / MIDI EXPORT")
        self._line(13, "[7] TULIP WORLD PUBLIC LOUNGE - READ ONLY HERE")
        self._line(15, "[R] REFRESH RELAY")
        online = self.data.get("online", [])
        self._line(18, "CAPTAINS CURRENTLY DOCKED", self.ACCENT)
        if online:
            for index, captain in enumerate(online[:12]):
                self._line(20 + index, "%-22s %s" % (captain.get("callsign", "ANON"), captain.get("activity", "DOCKED")))
        else:
            self._line(20, "NO OTHER ACTIVE SIGNALS AT THIS STATION.", self.DIM)
        self._footer("[1-7] SELECT TERMINAL   [R] REFRESH   // TOUCH KEYPAD READY")

    def draw_status(self):
        self._header("SHIP STATUS")
        player = self.data.get("player", {})
        self._line(4, "SHIP: %s" % player.get("ship_name", "LOST TULIP"), self.BRIGHT)
        self._line(5, "CALLSIGN: %s" % player.get("callsign", self.local["callsign"]))
        self._line(6, "SYSTEM: %s" % player.get("system_name", "UNKNOWN"))
        self._line(7, "CREDITS: %s" % player.get("credits", 0))
        self._line(8, "FUEL: %s / 100" % player.get("fuel", 0))
        self._line(9, "HULL: %s / 100" % player.get("hull", 0))
        self._line(10, "SHIELD: %s / 100" % player.get("shield", 0))
        self._line(12, "CARGO HOLD", self.ACCENT)
        cargo = player.get("cargo", {})
        items = self.data.get("universe", {}).get("commodities", [])
        for index, item in enumerate(items):
            self._line(14 + index, "%-18s %3d" % (item.get("name", item.get("id", "ITEM")), cargo.get(item.get("id"), 0)))
        self._footer()

    def draw_navigation(self):
        self._header("NAVIGATION")
        player = self.data.get("player", {})
        self._line(4, "CURRENT SYSTEM: %s  //  FUEL: %s" % (player.get("system_name", "UNKNOWN"), player.get("fuel", 0)), self.BRIGHT)
        self._line(6, "SELECT A DESTINATION. THE RELAY CALCULATES FUEL AND ENCOUNTERS.", self.DIM)
        for index, system in enumerate(self.nav_systems):
            marker = "*" if system.get("id") == player.get("system") else " "
            self._line(8 + index, "[%d] %s %-22s  TYPE %-12s  DANGER %s" % (
                index + 1,
                marker,
                system.get("name", "UNKNOWN"),
                system.get("type", "SPACE"),
                system.get("danger", 1),
            ))
        self._footer("[1-9] WARP   [0] BACK")

    def draw_market(self):
        self._header("COMMODITY EXCHANGE")
        player = self.data.get("player", {})
        self._line(4, "CREDITS: %s  //  SELECT ITEM, THEN BUY OR SELL ONE UNIT" % player.get("credits", 0), self.BRIGHT)
        if not self.market_items:
            self._line(7, "NO MARKET DATA. PRESS [R] TO REFRESH.", self.ALERT)
        for index, item in enumerate(self.market_items[:8]):
            selected = ">" if index == self.market_selected else " "
            cargo = player.get("cargo", {}).get(item.get("id"), 0)
            self._line(7 + index, "%s[%d] %-16s BUY %5d  SELL %5d  HOLD %3d" % (
                selected,
                index + 1,
                item.get("name", item.get("id", "ITEM")),
                item.get("buy", 0),
                item.get("sell", 0),
                cargo,
            ), self.BRIGHT if selected == ">" else self.FG)
        self._footer("[1-8] SELECT   [B] BUY 1   [S] SELL 1   [R] REFRESH   [0] BACK")

    def draw_combat(self):
        self._header("DEEP-SPACE OPERATIONS")
        battle = self.data.get("battle")
        player = self.data.get("player", {})
        if battle and battle.get("active"):
            self._line(4, "HOSTILE CONTACT: %s" % battle.get("enemy_name", "ALIEN"), self.ALERT)
            self._line(6, "ENEMY HULL   %3d / %3d" % (battle.get("enemy_hull", 0), battle.get("enemy_max_hull", 100)))
            self._line(7, "YOUR HULL    %3d / 100" % player.get("hull", 0))
            self._line(8, "YOUR SHIELD  %3d / 100" % player.get("shield", 0))
            self._line(11, "[F] FIRE PULSE CANNONS")
            self._line(12, "[D] DIVERT POWER TO SHIELDS")
            self._line(13, "[R] EMERGENCY RETREAT")
            self._line(16, battle.get("log", "THE SIGNAL SCREAMS THROUGH THE VOID."), self.ACCENT)
            self._footer("[F] FIRE   [D] DEFEND   [R] RETREAT   [0] BACK")
        else:
            self._line(5, "NO ACTIVE HOSTILE CONTACT.", self.GOOD)
            self._line(7, "[S] SCAN FOR SIGNALS, SALVAGE, TRADERS, AND ALIENS")
            event = self.data.get("event")
            if event:
                self._line(10, event.get("title", "LAST SCAN"), self.ACCENT)
                self._line(11, event.get("text", ""))
            self._footer("[S] SCAN   [0] BACK")

    def draw_chat(self):
        self._header("STATION CHAT")
        player = self.data.get("player", {})
        self._line(4, "LOCAL BOARD: %s // MANUAL POSTS ONLY" % player.get("system_name", "UNKNOWN"), self.BRIGHT)
        start = max(0, len(self.chat_messages) - 16)
        y = 6
        for item in self.chat_messages[start:]:
            text = "<%s> %s" % (item.get("callsign", "ANON"), item.get("message", ""))
            self._line(y, text)
            y += 1
        if not self.chat_messages:
            self._line(7, "THE STATION BOARD IS SILENT.", self.DIM)
        if self.composing:
            self._line(42, "> " + self.compose_text + "_", self.BRIGHT, 17)
            self._footer("TYPE MESSAGE   ENTER SENDS   ESC CANCELS")
        else:
            self._footer("[T] TYPE MESSAGE   [R] REFRESH   [0] BACK")

    def draw_tracker(self):
        self._header("ELEMENT115 TRACKER")
        self._line(4, "JUNO PATCH %03d  BPM %03d  PLAY %s  MIDI OUT %s" % (
            self.tracker.patch,
            self.tracker.bpm,
            "YES" if self.tracker.playing else "NO",
            "YES" if self.tracker.midi_thru else "NO",
        ), self.BRIGHT)
        self._line(5, "AMBIENT UNLOADED // HARD CAP: 6 SIMULTANEOUS JUNO NOTES", self.GOOD)
        for index, row in enumerate(self.tracker.rows_for_display()):
            self._line(8 + index, row, self.BRIGHT if index == self.tracker.row else self.FG)
        self._line(18, "CURSOR +/@   NOTE X   PLAYHEAD :/*", self.DIM)
        self._line(20, "[W/S] ROW   [[/]] STEP   [-/+] NOTE   [SPACE] TOGGLE")
        self._line(21, "[R] RANDOMIZE   [P] PLAY/STOP   [M] MIDI OUT   [E] EXPORT .MID")
        self._line(22, "[,] BPM -/+  //  WEB DOWNLOADS; HARDWARE SAVES LOCALLY")
        if self.tracker.last_export:
            status = "BROWSER DOWNLOADED" if self.tracker.last_browser_download else "SAVED LOCALLY"
            self._line(25, "LAST EXPORT: %s // %s" % (self.tracker.last_export, status), self.GOOD)
        self._footer("[0] BACK   TOUCH CONTROLS ACTIVE   AMY AUDIO ONLY")

    def draw_world(self):
        self._header("TULIP WORLD PUBLIC LOUNGE")
        self._line(4, "READ-ONLY INSIDE TULIPWARS. NOTHING IS POSTED AUTOMATICALLY.", self.GOOD)
        self._line(5, "USE run('worldui') SEPARATELY WHEN YOU CHOOSE TO CHAT PUBLICLY.", self.DIM)
        y = 7
        if self.world_messages:
            for item in self.world_messages[-12:]:
                self._line(y, "<%s> %s" % (item.get("username", "ANON"), item.get("content", "")))
                y += 1
        else:
            self._line(8, "PRESS [R] TO READ THE LATEST PUBLIC TULIP WORLD MESSAGES.")
        self._line(23, "MANUAL PACKAGE UPDATE COMMAND", self.ACCENT)
        if tw_config.WORLD_AUTHOR:
            command = "world.download('%s','%s')" % (tw_config.WORLD_PACKAGE, tw_config.WORLD_AUTHOR)
        else:
            command = "world.download('%s')" % tw_config.WORLD_PACKAGE
        self._line(25, command, self.BRIGHT)
        self._line(27, "THE GAME NEVER CALLS world.post_message().", self.GOOD)
        self._footer("[R] READ PUBLIC LOUNGE   [0] BACK")

    def key(self, code):
        if self.composing:
            self._chat_key(code)
            return
        if code in (48,):  # 0
            if self.screen == "tracker":
                self._leave_tracker()
            else:
                self.screen = "home"
            self.draw()
            return
        try:
            char = chr(code)
        except Exception:
            return
        upper = char.upper()

        if self.screen == "configure":
            return
        if self.screen == "offline":
            if upper == "R":
                self.connect()
            elif char == "6":
                self._enter_tracker()
                self.draw()
            return
        if self.screen == "home":
            self._key_home(char, upper)
        elif self.screen == "navigation":
            self._key_navigation(char)
        elif self.screen == "market":
            self._key_market(char, upper)
        elif self.screen == "combat":
            self._key_combat(upper)
        elif self.screen == "chat":
            self._key_chat(upper)
        elif self.screen == "tracker":
            self._key_tracker(char, upper)
        elif self.screen == "world":
            if upper == "R":
                self.read_world()

    def _key_home(self, char, upper):
        if char == "1":
            self.screen = "status"
        elif char == "2":
            self.screen = "navigation"
        elif char == "3":
            self.screen = "market"
            self._call(self.client.market)
        elif char == "4":
            self.screen = "combat"
        elif char == "5":
            self.screen = "chat"
            self._call(self.client.chat_list)
        elif char == "6":
            self._enter_tracker()
        elif char == "7":
            self.screen = "world"
        elif upper == "R":
            self._call(self.client.status)
        self.draw()

    def _key_navigation(self, char):
        if char >= "1" and char <= "9":
            index = ord(char) - ord("1")
            if index < len(self.nav_systems):
                destination = self.nav_systems[index]
                self._call(
                    self.client.travel,
                    destination.get("id"),
                    after=lambda response: self.audio.sfx("warp"),
                )
        self.draw()

    def _key_market(self, char, upper):
        if char >= "1" and char <= "8":
            index = ord(char) - ord("1")
            if index < len(self.market_items):
                self.market_selected = index
        elif upper == "R":
            self._call(self.client.market)
        elif upper in ("B", "S") and self.market_items:
            item = self.market_items[self.market_selected]
            side = "buy" if upper == "B" else "sell"
            self._call(self.client.trade, item.get("id"), side, 1)
        self.draw()

    def _key_combat(self, upper):
        battle = self.data.get("battle")
        if battle and battle.get("active"):
            command = None
            if upper == "F":
                command = "fire"
                self.audio.sfx("laser")
            elif upper == "D":
                command = "defend"
            elif upper == "R":
                command = "retreat"
            if command:
                def combat_done(response):
                    if response.get("damage_taken", 0) > 0:
                        self.audio.sfx("damage")
                self._call(self.client.combat, command, after=combat_done)
        elif upper == "S":
            self._call(self.client.scan)
        self.draw()

    def _key_chat(self, upper):
        if upper == "R":
            self._call(self.client.chat_list)
        elif upper == "T":
            self.composing = True
            self.compose_text = ""
        self.draw()

    def _chat_key(self, code):
        if code in (10, 13):
            text = self.compose_text.strip()
            self.composing = False
            self.compose_text = ""
            if text:
                self._call(self.client.chat_post, text)
            self.draw()
            return
        if code == 27:
            self.composing = False
            self.compose_text = ""
            self.draw()
            return
        if code in (8, 127):
            self.compose_text = self.compose_text[:-1]
            self.draw()
            return
        if 32 <= code <= 126 and len(self.compose_text) < 80:
            self.compose_text += chr(code)
            self.draw()

    def _key_tracker(self, char, upper):
        redraw = True
        if upper == "W":
            self.tracker.move_row(-1)
        elif upper == "S":
            self.tracker.move_row(1)
        elif char == "[":
            self.tracker.move_step(-1)
        elif char == "]":
            self.tracker.move_step(1)
        elif char in ("-", "_"):
            self.tracker.change_note(-1)
        elif char in ("+", "="):
            self.tracker.change_note(1)
        elif char == ",":
            self.tracker.change_bpm(-1)
        elif char == ".":
            self.tracker.change_bpm(1)
        elif char == " ":
            self.tracker.toggle()
        elif upper == "R":
            was_playing = self.tracker.playing
            self.tracker.stop()
            self.tracker.release()
            self.tracker.randomize()
            if was_playing:
                self.tracker.start()
        elif upper == "P":
            if self.tracker.playing:
                self.tracker.stop()
            else:
                self.tracker.start()
        elif upper == "M":
            self.tracker.midi_thru = not self.tracker.midi_thru
        elif upper == "E":
            try:
                path, downloaded = self.tracker.export()
                if downloaded:
                    self.message = "MIDI EXPORTED AND DOWNLOADED: %s" % path
                else:
                    self.message = "MIDI EXPORTED LOCALLY: %s" % path
            except Exception as exc:
                self.message = "MIDI EXPORT FAILED: %s" % exc
        else:
            redraw = False
        if redraw:
            self.draw()

    def read_world(self):
        try:
            if tulip.board() in ("WEB", "AMYBOARD_WEB"):
                self.message = "TULIP WEB USES ASYNC WORLD ACCESS; OPEN worldui DIRECTLY."
            else:
                import world
                messages = world.messages(n=12, mtype="text")
                messages.reverse()
                self.world_messages = messages
                self.message = "PUBLIC LOUNGE READ. NO MESSAGE WAS POSTED."
                self.online = True
        except Exception as exc:
            self.message = "WORLD READ FAILED: %s" % exc
        self.draw()

    def tick(self):
        now = tulip.ticks_ms()
        if self.screen == "tracker":
            # AmbientEngine is fully released for the entire tracker screen,
            # even while playback is stopped and the user is only editing.
            if self.tracker.playing:
                advanced = self.tracker.tick(now)
                if advanced and now - self.last_tracker_redraw > 40:
                    self.last_tracker_redraw = now
                    self.draw()
        else:
            if self.audio_fault is None:
                try:
                    self.audio.tick(now)
                except Exception as exc:
                    # A platform audio-clock difference must never flood the
                    # frame callback with tracebacks or make the game unusable.
                    self.audio_fault = str(exc)
                    self.audio.stop()
                    self.message = "AMY SAFETY STOP: %s" % self.audio_fault
                    self.draw()

        if self.online and now - self.last_heartbeat >= tw_config.HEARTBEAT_MS:
            self.last_heartbeat = now
            # This heartbeat goes only to the user's private PHP host.
            # It never touches Tulip World.
            if self.screen not in ("chat", "tracker") and not self.heartbeat_pending and not self.request_pending:
                self.heartbeat_pending = True

                def heartbeat_ok(response):
                    self.heartbeat_pending = False
                    self._apply(response)
                    self.online = True

                def heartbeat_fail(_exc):
                    self.heartbeat_pending = False
                    self.online = False

                self.client.heartbeat(done=heartbeat_ok, fail=heartbeat_fail)


def _fatal_screen(exc):
    # Keep failures visible on Tulip Web/hardware instead of leaving a black app.
    try:
        tulip.gpu_reset()
        tulip.tfb_start()
        tulip.tfb_font(0)
        tulip.bg_clear(0)
        message = str(exc).replace("\n", " ")
        lines = [
            "=" * 128,
            " TULIPWARS 2026 // STARTUP ERROR ",
            "=" * 128,
            "",
            "THE DISPLAY IS WORKING, BUT STARTUP HIT AN ERROR:",
            message[:128],
            "",
            "REFRESH TULIP WEB, THEN RUN THE FULL INSTALLER AGAIN.",
        ]
        for y, text in enumerate(lines):
            tulip.tfb_str(0, y, text + (" " * max(0, 128 - len(text))), 0, 231 if y != 5 else 196, 0)
    except Exception:
        pass


def activate(app):
    global GAME
    try:
        if BOOT_ERROR is not None:
            raise BOOT_ERROR
        _load_modules(app)
        if GAME is None:
            GAME = TulipWarsGame(app)
        GAME.start()
        tulip.keyboard_callback(on_key)
        tulip.touch_callback(on_touch)
        tulip.frame_callback(on_frame, app)
    except Exception as exc:
        _fatal_screen(exc)


def deactivate(app):
    tulip.keyboard_callback()
    try:
        tulip.touch_callback()
    except Exception:
        pass
    tulip.frame_callback()
    if GAME is not None:
        GAME.stop()


def quit_app(app):
    deactivate(app)


def on_key(code):
    if GAME is not None:
        GAME.key(code)


def on_touch(up):
    if GAME is not None:
        GAME.touch(up)


def on_frame(app):
    if not getattr(app, "active", True):
        return
    if GAME is not None:
        try:
            GAME.tick()
        except Exception as exc:
            # Last-resort frame guard: stop audio and keep the terminal alive.
            try:
                GAME.audio.stop()
                GAME.message = "FRAME SAFETY STOP: %s" % exc
                GAME.draw()
            except Exception:
                pass


def run(app):
    global APP, BOOT_ERROR
    APP = app
    BOOT_ERROR = None
    _prepare_module_path(app)
    try:
        # Import while Tulip is still inside the package loader. The explicit
        # path remains available later when the UIScreen activates.
        _load_modules(app)
    except Exception as exc:
        BOOT_ERROR = exc
    app.game = True

    # Tulip UIScreens hide the text framebuffer by default. TulipWars draws its
    # entire console on that framebuffer, so keeping it visible is mandatory.
    app.keep_tfb = True
    app.bg_color = 0
    app.offset_y = 0

    # Keep the task bar visible in Tulip Web while testing. Hardware/Desktop
    # retain the intended full-screen game presentation.
    try:
        app.hide_task_bar = tulip.board() != "WEB"
    except Exception:
        app.hide_task_bar = False

    app.activate_callback = activate
    app.deactivate_callback = deactivate
    app.quit_callback = quit_app
    app.present()
