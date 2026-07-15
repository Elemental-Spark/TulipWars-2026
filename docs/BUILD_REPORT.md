# TulipWars 2026 v0.1.10 build report

- PASS: All game, installer, and hardware-updater Python files compile.
- PASS: Hardware helper contains real newlines and executable code (not escaped one-line text).
- PASS: Installer embedded files match readable v0.1.10 source byte-for-byte.
- PASS: Missing _user_dir helper is restored.
- PASS: Exact full installer executes, launches, preserves identity/MIDI/config, and replaces obsolete code.
- PASS: Friendly-REPL chunk protocol reconstructs the exact complete installer.
- PASS: All PHP files pass PHP lint.
- PASS: Website package excludes live data/state.json.
- PASS: Physical updater drains stale REPL prompts before identification.
- PASS: Friendly-REPL wake and command exchange passed serial-state simulation.
- PASS: Physical transfer uses pyserial commands and no mpremote execution.
