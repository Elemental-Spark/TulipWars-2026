# Features and changes

```text
TULIPWARS 2026 v0.1.8 FEATURES AND CHANGES
===========================================

HARDWARE AUDIO SAFETY
- Six managed Juno voices maximum throughout the game.
- Procedural ambient music uses four Juno voices.
- Ambient chords reuse the same voice pool instead of overlapping.
- Interface sounds share one short AMY oscillator.
- Entering Element115 Tracker sends ambient notes off and releases its PatchSynth.
- Ambient remains unloaded while editing or playing in the tracker.
- Tracker uses exactly six managed Juno voices.
- Dense eight-row patterns rotate lanes while playing at most six notes per step.
- Leaving the tracker releases its synth before ambience is rebuilt.

ELEMENT115 TRACKER
- Eight rows and sixteen steps.
- Procedural Lost Signal pattern generation.
- Juno patch randomization.
- Adjustable notes and tempo.
- AMY playback and optional hardware MIDI output.
- Standard MIDI type-0 export.
- Automatic browser .MID download in Tulip Web.
- Local .MID storage on physical Tulip and Desktop.

CORE GAME
- Anonymous persistent ship identity.
- Nine explorable star systems.
- Space travel, fuel use, scans, salvage, traders, and alien encounters.
- Dynamic station markets, cargo, credits, hull, and shields.
- Turn-based alien combat.
- Anonymous station-local BBS chat and active-captain presence.
- Read-only Tulip World lounge with no automatic posts.
- AMY-only procedural music and sound effects; no audio samples.

```
