import json
import os
import random


def _exists(path):
    try:
        os.stat(path)
        return True
    except Exception:
        return False


def _hex_byte(value):
    return ("%02X" % (int(value) & 255))


def _entropy_hex(byte_count=8):
    # Tulip Web's MicroPython random.getrandbits() accepts at most 32 bits.
    # Prefer os.urandom, but never request a >32-bit random integer fallback.
    try:
        raw = os.urandom(byte_count)
        return "".join(_hex_byte(raw[index]) for index in range(len(raw)))
    except Exception:
        parts = []
        while len(parts) < byte_count:
            try:
                value = random.getrandbits(32)
            except Exception:
                value = random.randint(0, 0x7FFFFFFF)
            parts.extend((
                (value >> 24) & 255,
                (value >> 16) & 255,
                (value >> 8) & 255,
                value & 255,
            ))
        return "".join(_hex_byte(value) for value in parts[:byte_count])


def make_identity(prefix="TULIP"):
    # Anonymous persistent installation identity. It is not an account and is
    # never associated with an email, password, profile, or login API.
    device_id = _entropy_hex(8)
    callsign = "%s-%s" % (prefix, device_id[-4:])
    return {"device_id": device_id, "callsign": callsign}


def load(app_dir, prefix="TULIP"):
    path = app_dir + "/local_state.json"
    if _exists(path):
        try:
            with open(path, "r") as handle:
                data = json.load(handle)
            if data.get("device_id") and data.get("callsign"):
                return data
        except Exception:
            pass
    data = make_identity(prefix)
    save(app_dir, data)
    return data


def save(app_dir, data):
    path = app_dir + "/local_state.json"
    with open(path, "w") as handle:
        json.dump(data, handle)
    return path
