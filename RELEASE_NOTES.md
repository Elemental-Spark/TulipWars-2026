# TulipWars 2026 v0.1.8 — Hardware Audio + MIDI Download Update

The new public update is ready for Tulip Web, Desktop, and physical Tulip hardware.

## What changed

- Hard six-voice Juno limit to prevent AMY overload warning tones on hardware
- Procedural ambience reduced to four voices with no overlapping ambient chords
- Opening Element115 Tracker completely unloads the background synth
- Tracker playback capped to six simultaneous notes, even with all eight lanes active
- Leaving Tracker safely releases its synth before ambience returns
- Tulip Web now downloads exported `.mid` files directly to your browser
- Physical Tulip/Desktop still save MIDI files locally

## Install or update

1. Open Tulip Web and choose **Show code editor**.
2. Upload `INSTALL_OR_UPDATE_TULIPWARS_v0.1.8.py`.
3. Load it and click the green **Run** button.

The one-file updater preserves your anonymous ship identity, progress, relay configuration, and existing Element115 MIDI exports.

Physical Tulip users on Windows can use the included one-click hardware updater in the `HARDWARE_UPDATE` folder.

TulipWars uses no accounts or login API and never automatically posts messages or files to Tulip World.


## Validation

- Python source and embedded installer compiled successfully.
- PHP files passed lint.
- Dense eight-row tracker playback was simulated and emitted exactly six note-ons.
- Ambient allocation was simulated at four voices and released fully on tracker entry.
- Browser MIDI download bridge and Standard MIDI file structure were validated.

Physical Tulip v0.1.8 audio behavior still needs public confirmation; v0.1.7 is the last user-confirmed hardware-run baseline.
