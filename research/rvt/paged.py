"""Clean-room Revit stored-page parity encoder, derived from licensed RVT bytes.

Each full page contains 64896 bytes, 12 zero bits, 2805 parity bits, and 7
zero bits (all bits LSB-first). The 519180 data/padding bits are interleaved
into 255 lanes of 2036 bits. Each lane is a systematic binary cyclic
(2047,2036) code with generator x^11+x^2+1, in transmission order.
"""
from pages import PAYLOAD, STORED

LANES = 255
DATA_WORDS = 2036
PARITY_WORDS = 11
GENERATOR = 0x805
MASK = (1 << LANES) - 1


def trailer(payload: bytes) -> bytes:
    if len(payload) != PAYLOAD:
        raise ValueError(f'full-page payload must be {PAYLOAD} bytes')
    value = int.from_bytes(payload, 'little')
    state = [0] * PARITY_WORDS
    for _ in range(DATA_WORDS):
        feedback = (value & MASK) ^ state[-1]
        value >>= LANES
        state = [feedback] + state[:-1]
        state[2] ^= feedback
    parity = 0
    for word in state:
        parity = (parity << LANES) | word
    return (parity << 12).to_bytes(STORED - PAYLOAD, 'little')


def encode(data: bytes) -> bytes:
    out = bytearray()
    for start in range(0, len(data), PAYLOAD):
        block = data[start:start + PAYLOAD]
        out.extend(block)
        if len(block) == PAYLOAD:
            out.extend(trailer(block))
    return bytes(out)


def decode(stored: bytes, *, verify: bool = True) -> bytes:
    out = bytearray()
    full = len(stored) // STORED
    for index in range(full):
        block = stored[index * STORED:(index + 1) * STORED]
        payload = block[:PAYLOAD]
        if verify and trailer(payload) != block[PAYLOAD:]:
            raise ValueError(f'invalid parity or padding on page {index}')
        out.extend(payload)
    remainder = stored[full * STORED:]
    if len(remainder) >= PAYLOAD:
        raise ValueError('ambiguous/truncated final page: full payload without full parity')
    out.extend(remainder)
    return bytes(out)
