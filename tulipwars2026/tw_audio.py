import random
import tulip
import amy
import synth


def _audio_ticks_ms():
    """Return a usable AMY scheduling clock on hardware, Desktop, and Web."""
    try:
        fn = getattr(tulip, "amy_ticks_ms", None)
        if callable(fn):
            return int(fn())
    except Exception:
        pass
    try:
        fn = getattr(tulip, "ticks_ms", None)
        if callable(fn):
            return int(fn())
    except Exception:
        pass
    return 0


class AmbientEngine:
    """AMY-only procedural LOST SIGNALS-inspired Juno ambience.

    Hardware rule: never allocate more than six Juno voices. The ambient bed
    deliberately uses only four, leaving headroom for Tulip itself and for the
    short single-oscillator interface effects.
    """

    MAX_JUNO_VOICES = 6
    AMBIENT_VOICES = 4
    SFX_OSC = 119

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
        self.suspended = False

    def _configure_fx(self):
        try:
            amy.reverb(0.62)
            amy.echo(level=0.16, delay_ms=random.choice([620, 740, 860, 980]), feedback=0.38)
        except Exception:
            pass

    def _all_off(self):
        if self.synth is not None:
            try:
                self.synth.all_notes_off()
            except Exception:
                pass
        self.pending_off = []

    def _release_synth(self):
        self._all_off()
        if self.synth is not None:
            try:
                self.synth.release()
            except Exception:
                pass
        self.synth = None

    def _new_synth(self):
        # Release the old Juno allocation before requesting another one. This is
        # essential on Tulip hardware, where overlapping PatchSynth allocations
        # can trigger AMY overload warning tones.
        self._release_synth()
        self.patch = random.choice(self.JUNO_PATCHES)
        try:
            self.synth = synth.PatchSynth(num_voices=self.AMBIENT_VOICES, patch=self.patch)
        except Exception:
            self.synth = None

    def start(self):
        self.enabled = True
        self.suspended = False
        self._configure_fx()
        self._new_synth()
        self.next_chord_ms = tulip.ticks_ms() + 600

    def suspend(self):
        """Completely unload the ambient Juno while another console owns AMY."""
        self.enabled = False
        self.suspended = True
        self._release_synth()

    def pause(self):
        # Kept as a compatibility alias for older callers.
        self.suspend()

    def resume(self):
        self.enabled = True
        self.suspended = False
        self._configure_fx()
        if self.synth is None:
            self._new_synth()
        self.next_chord_ms = tulip.ticks_ms() + 700

    def stop(self):
        self.enabled = False
        self.suspended = False
        self._release_synth()
        # Do not reset AMY globally; another Tulip app may be sounding.

    def tick(self, now_ms):
        if self.synth is None or not self.enabled or self.suspended:
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
        if self.chord_count % random.choice([4, 5, 6]) == 0:
            self._new_synth()
            if self.synth is None:
                return

        # Reuse the same four managed voices instead of allowing long Juno
        # releases from one chord to overlap a second chord.
        self._all_off()
        root = random.choice(self.ROOTS)
        chord = random.choice(self.CHORDS)
        spread = random.choice([0, 0, 12])
        duration = random.randint(6500, 10500)
        amy_now = _audio_ticks_ms()
        for index, interval in enumerate(chord[:self.AMBIENT_VOICES]):
            note = root + interval + (spread if index >= 2 else 0)
            velocity = 0.09 + (random.random() * 0.10)
            try:
                self.synth.note_on(note, velocity, time=amy_now + index * random.randint(120, 340))
                self.pending_off.append((now_ms + duration + index * 120, note))
            except Exception:
                pass
        self.next_chord_ms = now_ms + random.randint(9000, 15000)

    def sfx(self, kind="ok"):
        # One reusable oscillator prevents interface sounds from accumulating.
        # Tracker mode intentionally skips these effects to keep its six Juno
        # voices exclusive on hardware.
        if self.suspended:
            return
        try:
            now = _audio_ticks_ms()
            amy.send(osc=self.SFX_OSC, vel=0, time=now)
            if kind == "laser":
                amy.send(osc=self.SFX_OSC, wave=amy.SAW_DOWN, note=82, vel=0.22, time=now + 2)
                amy.send(osc=self.SFX_OSC, note=55, time=now + 80)
                amy.send(osc=self.SFX_OSC, vel=0, time=now + 190)
            elif kind == "damage":
                amy.send(osc=self.SFX_OSC, wave=amy.NOISE, vel=0.18, time=now + 2)
                amy.send(osc=self.SFX_OSC, vel=0, time=now + 180)
            elif kind == "warp":
                amy.send(osc=self.SFX_OSC, wave=amy.SINE, note=42, vel=0.18, time=now + 2)
                amy.send(osc=self.SFX_OSC, note=76, time=now + 260)
                amy.send(osc=self.SFX_OSC, vel=0, time=now + 580)
            else:
                amy.send(osc=self.SFX_OSC, wave=amy.SINE, note=76, vel=0.13, time=now + 2)
                amy.send(osc=self.SFX_OSC, vel=0, time=now + 95)
        except Exception:
            pass
