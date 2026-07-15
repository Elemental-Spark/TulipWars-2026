import random
import tulip
import amy
import synth


class AmbientEngine:
    """AMY-only procedural LOST SIGNALS-inspired Juno ambience."""

    JUNO_PATCHES = [0, 1, 5, 11, 18, 24, 32, 40, 48, 56, 64, 72, 80, 88, 96, 104, 112, 120]
    ROOTS = [34, 36, 38, 41, 43, 45]
    CHORDS = [
        [0, 3, 7, 10],
        [0, 5, 7, 12],
        [0, 2, 7, 9],
        [0, 3, 8, 12],
        [0, 7, 10, 15],
    ]

    def __init__(self):
        self.synth = None
        self.patch = None
        self.next_chord_ms = 0
        self.pending_off = []
        self.chord_count = 0
        self.enabled = True

    def _new_synth(self):
        if self.synth is not None:
            try:
                self.synth.release()
            except Exception:
                pass
        self.patch = random.choice(self.JUNO_PATCHES)
        try:
            self.synth = synth.PatchSynth(num_voices=6, patch=self.patch)
        except Exception:
            self.synth = None

    def start(self):
        self.enabled = True
        try:
            amy.reverb(0.72)
            amy.echo(level=0.22, delay_ms=random.choice([620, 740, 860, 980]), feedback=0.48)
        except Exception:
            pass
        self._new_synth()
        self.next_chord_ms = tulip.ticks_ms() + 600

    def pause(self):
        self.enabled = False
        self._all_off()

    def resume(self):
        self.enabled = True
        self.next_chord_ms = tulip.ticks_ms() + 300

    def _all_off(self):
        if self.synth is not None:
            try:
                self.synth.all_notes_off()
            except Exception:
                pass
        self.pending_off = []

    def stop(self):
        self.enabled = False
        self._all_off()
        if self.synth is not None:
            try:
                self.synth.release()
            except Exception:
                pass
        self.synth = None
        # Do not reset AMY globally; another Tulip app may be sounding.

    def tick(self, now_ms):
        if self.synth is None or not self.enabled:
            return
        keep = []
        for off_ms, note in self.pending_off:
            if now_ms >= off_ms:
                try:
                    self.synth.note_off(note)
                except Exception:
                    pass
            else:
                keep.append((off_ms, note))
        self.pending_off = keep

        if now_ms < self.next_chord_ms:
            return

        self.chord_count += 1
        if self.chord_count % random.choice([3, 4, 5]) == 0:
            self._new_synth()
            if self.synth is None:
                return

        root = random.choice(self.ROOTS)
        chord = random.choice(self.CHORDS)
        spread = random.choice([0, 0, 12])
        duration = random.randint(6500, 12000)
        amy_now = tulip.amy_ticks_ms()
        for index, interval in enumerate(chord):
            note = root + interval + (spread if index >= 2 else 0)
            velocity = 0.10 + (random.random() * 0.12)
            try:
                self.synth.note_on(note, velocity, time=amy_now + index * random.randint(120, 420))
                self.pending_off.append((now_ms + duration + index * 150, note))
            except Exception:
                pass
        self.next_chord_ms = now_ms + random.randint(8500, 15500)

    def sfx(self, kind="ok"):
        # High oscillator IDs avoid the managed Juno voice pool in normal use.
        try:
            now = tulip.amy_ticks_ms()
            if kind == "laser":
                amy.send(osc=116, wave=amy.SAW_DOWN, note=82, vel=0.28, time=now)
                amy.send(osc=116, note=55, time=now + 90)
                amy.send(osc=116, vel=0, time=now + 220)
            elif kind == "damage":
                amy.send(osc=117, wave=amy.NOISE, vel=0.24, time=now)
                amy.send(osc=117, vel=0, time=now + 240)
            elif kind == "warp":
                amy.send(osc=118, wave=amy.SINE, note=42, vel=0.22, time=now)
                amy.send(osc=118, note=78, time=now + 320)
                amy.send(osc=118, vel=0, time=now + 700)
            else:
                amy.send(osc=119, wave=amy.SINE, note=76, vel=0.18, time=now)
                amy.send(osc=119, vel=0, time=now + 120)
        except Exception:
            pass
