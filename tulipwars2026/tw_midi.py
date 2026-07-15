# Minimal Standard MIDI File type-0 exporter for the Element115 console.


def _u16(value):
    return bytes([(value >> 8) & 255, value & 255])


def _u32(value):
    return bytes([
        (value >> 24) & 255,
        (value >> 16) & 255,
        (value >> 8) & 255,
        value & 255,
    ])


def _vlq(value):
    value = int(value)
    out = [value & 0x7F]
    value >>= 7
    while value:
        out.insert(0, (value & 0x7F) | 0x80)
        value >>= 7
    return bytes(out)


def export_midi(pattern, notes, bpm, filename, program=0):
    ppqn = 96
    step_ticks = ppqn // 4  # sixteenth notes
    gate_ticks = int(step_ticks * 0.72)
    tempo = int(60000000 / max(30, min(300, bpm)))

    events = []
    # order 0 note-offs before order 1 note-ons when sharing a timestamp.
    events.append((0, -2, bytes([0xFF, 0x51, 0x03, (tempo >> 16) & 255, (tempo >> 8) & 255, tempo & 255])))
    events.append((0, -1, bytes([0xC0, program & 0x7F])))

    for row in range(len(pattern)):
        note = int(notes[row]) & 0x7F
        for step in range(len(pattern[row])):
            if pattern[row][step]:
                tick = step * step_ticks
                velocity = max(28, 92 - row * 5)
                events.append((tick, 1, bytes([0x90, note, velocity])))
                events.append((tick + gate_ticks, 0, bytes([0x80, note, 0])))

    events.sort(key=lambda item: (item[0], item[1]))
    track = bytearray()
    last_tick = 0
    for tick, _order, data in events:
        track.extend(_vlq(tick - last_tick))
        track.extend(data)
        last_tick = tick

    end_tick = 16 * step_ticks
    track.extend(_vlq(max(0, end_tick - last_tick)))
    track.extend(bytes([0xFF, 0x2F, 0x00]))

    header = b"MThd" + _u32(6) + _u16(0) + _u16(1) + _u16(ppqn)
    chunk = b"MTrk" + _u32(len(track)) + bytes(track)
    with open(filename, "wb") as handle:
        handle.write(header)
        handle.write(chunk)
    return filename


def _base64_file(filename):
    try:
        import ubinascii as binascii
    except Exception:
        import binascii
    with open(filename, "rb") as handle:
        data = handle.read()
    # MicroPython's b2a_base64 is most portable with RFC-sized chunks.
    encoded = []
    for offset in range(0, len(data), 57):
        part = binascii.b2a_base64(data[offset:offset + 57])
        if not isinstance(part, str):
            part = part.decode()
        encoded.append(part.strip())
    return "".join(encoded)


def download_in_browser(filename):
    """Start a real browser download in Tulip Web; no-op on hardware/Desktop."""
    try:
        import tulip
        if tulip.board() not in ("WEB", "AMYBOARD_WEB"):
            return False
        import js
        name = filename.rsplit("/", 1)[-1]
        href = "data:audio/midi;base64," + _base64_file(filename)
        anchor = js.document.createElement("a")
        anchor.setAttribute("href", href)
        anchor.setAttribute("download", name)
        anchor.setAttribute("style", "display:none")
        js.document.body.appendChild(anchor)
        anchor.click()
        js.document.body.removeChild(anchor)
        return True
    except Exception:
        # The local .mid remains safely exported even if a browser blocks the
        # download gesture or changes its JavaScript bridge.
        return False
