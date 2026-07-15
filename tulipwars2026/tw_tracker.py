import random
import tulip
import synth

import tw_midi


class Element115Tracker:
    ROWS = 8
    STEPS = 16
    MAX_JUNO_VOICES = 6
    PATCHES = [0, 1, 5, 11, 18, 24, 32, 40, 48, 56, 64, 72, 80, 96, 112, 120]

    def __init__(self, app_dir):
        self.app_dir = app_dir
        self.pattern = [[False for _ in range(self.STEPS)] for _ in range(self.ROWS)]
        self.notes = [36, 43, 48, 51, 55, 60, 63, 67]
        self.row = 0
        self.step = 0
        self.play_step = 0
        self.bpm = 72
        self.playing = False
        self.midi_thru = False
        self.next_step_ms = 0
        self.pending_off = []
        self.synth = None
        self.patch = random.choice(self.PATCHES)
        self.last_export = ""
        self.last_browser_download = False
        self.randomize()

    def randomize(self):
        root = random.choice([34, 36, 38, 41, 43])
        scale = [0, 3, 5, 7, 10, 12, 15, 17]
        self.notes = [root + scale[i] for i in range(self.ROWS)]
        for row in range(self.ROWS):
            density = 0.18 + row * 0.025
            for step in range(self.STEPS):
                anchor = step in (0, 4, 8, 12)
                self.pattern[row][step] = (random.random() < density) or (row == 0 and anchor and random.random() < 0.65)
        self.patch = random.choice(self.PATCHES)

    def toggle(self):
        self.pattern[self.row][self.step] = not self.pattern[self.row][self.step]

    def move_row(self, delta):
        self.row = (self.row + delta) % self.ROWS

    def move_step(self, delta):
        self.step = (self.step + delta) % self.STEPS

    def change_note(self, delta):
        self.notes[self.row] = max(24, min(96, self.notes[self.row] + delta))

    def change_bpm(self, delta):
        self.bpm = max(35, min(220, self.bpm + delta))

    def _ensure_synth(self):
        if self.synth is None:
            try:
                self.synth = synth.PatchSynth(num_voices=self.MAX_JUNO_VOICES, patch=self.patch)
            except Exception:
                self.synth = None

    def _rows_for_step(self, step):
        active = [row for row in range(self.ROWS) if self.pattern[row][step]]
        if len(active) <= self.MAX_JUNO_VOICES:
            return active
        # Rotate which two dense rows are omitted so all eight tracker lanes can
        # still be heard over time while hardware never receives >6 note-ons.
        offset = step % len(active)
        rotated = active[offset:] + active[:offset]
        return rotated[:self.MAX_JUNO_VOICES]

    def start(self):
        self._ensure_synth()
        if self.synth is not None:
            try:
                self.synth.all_notes_off()
            except Exception:
                pass
        self.pending_off = []
        self.playing = True
        self.play_step = 0
        self.next_step_ms = tulip.ticks_ms()

    def stop(self):
        self.playing = False
        if self.synth is not None:
            try:
                self.synth.all_notes_off()
            except Exception:
                pass
        self.pending_off = []
        if self.midi_thru:
            for note in self.notes:
                try:
                    tulip.midi_out([0x80, note & 127, 0])
                except Exception:
                    pass

    def release(self):
        self.stop()
        if self.synth is not None:
            try:
                self.synth.release()
            except Exception:
                pass
        self.synth = None

    def tick(self, now_ms):
        if self.synth is not None:
            keep = []
            for off_ms, note in self.pending_off:
                if now_ms >= off_ms:
                    try:
                        self.synth.note_off(note)
                    except Exception:
                        pass
                    if self.midi_thru:
                        try:
                            tulip.midi_out([0x80, note & 127, 0])
                        except Exception:
                            pass
                else:
                    keep.append((off_ms, note))
            self.pending_off = keep

        if not self.playing or now_ms < self.next_step_ms:
            return False

        self._ensure_synth()
        step_ms = int(60000 / self.bpm / 4)
        gate = max(40, int(step_ms * 0.62))
        for row in self._rows_for_step(self.play_step):
            note = self.notes[row]
            velocity = max(0.16, 0.42 - row * 0.022)
            if self.synth is not None:
                try:
                    self.synth.note_on(note, velocity)
                except Exception:
                    pass
            if self.midi_thru:
                try:
                    tulip.midi_out([0x90, note & 127, int(velocity * 127)])
                except Exception:
                    pass
            self.pending_off.append((now_ms + gate, note))

        self.play_step = (self.play_step + 1) % self.STEPS
        self.next_step_ms = now_ms + step_ms
        return True

    def export(self):
        try:
            suffix_value = random.getrandbits(16)
        except Exception:
            suffix_value = random.randint(0, 65535)
        suffix = "%04X" % suffix_value
        filename = self.app_dir + "/ELEMENT115_%s.mid" % suffix
        self.last_export = tw_midi.export_midi(self.pattern, self.notes, self.bpm, filename, self.patch)
        self.last_browser_download = tw_midi.download_in_browser(self.last_export)
        return self.last_export, self.last_browser_download

    def rows_for_display(self):
        lines = []
        for row in range(self.ROWS):
            cells = []
            for step in range(self.STEPS):
                active = self.pattern[row][step]
                if row == self.row and step == self.step:
                    cell = "@" if active else "+"
                elif self.playing and step == self.play_step:
                    cell = "*" if active else ":"
                else:
                    cell = "X" if active else "."
                cells.append(cell)
            lines.append("%d N%02d |%s|" % (row + 1, self.notes[row], "".join(cells)))
        return lines
