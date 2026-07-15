# TulipWars 2026 v0.1.8 Build Report

## Hardware audio corrections

- Ambient `PatchSynth` allocation reduced to four Juno voices.
- Global TulipWars managed-Juno ceiling is six voices.
- Ambient chords reuse the same four voices and stop the previous chord before the next.
- Interface effects share one short direct AMY oscillator rather than accumulating four effect oscillators.
- Opening Element115 Tracker calls `AmbientEngine.suspend()`, sends all notes off, releases the ambient `PatchSynth`, and leaves it unloaded while editing or playing.
- Tracker `PatchSynth` allocation reduced from eight voices to six.
- Dense tracker steps rotate through active lanes but emit no more than six simultaneous note-ons.
- Leaving the tracker releases its synth before rebuilding the ambient synth.

## MIDI improvements

- Standard MIDI type-0 export remains available on all targets.
- Tulip Web now creates a browser download using a MIDI data URI and a temporary download link.
- If a browser blocks the download, the `.mid` still remains in the Tulip package folder.
- Physical Tulip and Desktop continue saving MIDI locally.

## Distribution

- Complete one-file install/update package.
- Existing anonymous `local_state.json` is preserved.
- Existing `ELEMENT115_*.mid` files are preserved.
- Existing custom relay configuration is preserved instead of overwritten.
- Website/API and dashboard synchronized to v0.1.8.
- Live website `data/state.json` is intentionally excluded.
- No automatic Tulip World posts or uploads.

## Validation completed

- All Python files compiled successfully.
- Installer-embedded files match the readable source byte-for-byte.
- PHP files passed PHP lint.
- No eight-voice `PatchSynth` allocation remains.
- Simulated dense eight-row tracker step emitted exactly six note-ons.
- Simulated ambient engine allocated four voices and fully released on suspend.
- Simulated browser MIDI download created and clicked an `audio/midi` download link.
- Generated MIDI header and track chunk validated.
- Website download copy matches the public installer byte-for-byte.
- Website package contains no `data/state.json`.

Physical Tulip audio behavior still requires confirmation on the user’s device; v0.1.7 remains the last hardware-run baseline until v0.1.8 is tested there.
