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
