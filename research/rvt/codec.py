"""Byte-derived RVT page framing, including final-page length metadata.

Encoder profile: choose the smallest stored size among generators 4/5/6/7/9/11.
Historical files also contain unique valid layouts outside that encoder policy.
Use 65 lanes with shortened codewords, or odd lane counts with full codewords.
Reserve m+1 bits when choosing dimensions; the padding-count field occupies
max(7,m+1) bits. Small m may overlap zero high bits of the last payload byte;
nonzero overlap must select a larger layout, never discard input bits.
"""
from dataclasses import dataclass
from pages import PAYLOAD, STORED
from paged import trailer
from partial_pages import GENERATORS, identify, parity

@dataclass(frozen=True)
class Layout:
    lanes: int
    words: int
    generator: int

    @property
    def degree(self): return self.generator.bit_length()-1
    @property
    def data_bits(self): return (self.words-self.degree)*self.lanes
    @property
    def footer_bits(self): return max(7, self.degree+1)
    @property
    def size(self): return (self.lanes*self.words+7)//8


def candidates(size):
    if not 0 < size <= PAYLOAD: raise ValueError('page payload length outside 1..64896')
    out = set()
    for gen in GENERATORS:
        m = gen.bit_length()-1
        k = (1 << m)-1-m
        # The second reserve only affects tiny layouts whose footer could
        # overlap nonzero payload bits. Real gzip streams end in zero high bits.
        for reserve in (m+1, max(7, m+1)):
            needed = size*8+reserve
            if needed <= k*65:
                lanes, data_words = 65, (needed+64)//65
            else:
                lanes, data_words = ((needed+k-1)//k)|1, k
            if lanes <= 255:
                out.add(Layout(lanes, data_words+m, gen))
    return sorted(out, key=lambda x: (x.size, x.lanes, x.words, x.generator))


def padded_data(payload, layout):
    available = layout.data_bits-layout.footer_bits
    capacity = (available+7)//8
    padding = (capacity-len(payload))*8
    value = int.from_bytes(payload, 'little')
    if padding < 0 or padding >= 1 << layout.footer_bits or value >> available:
        raise ValueError('payload does not fit layout without losing bits')
    return value | (padding << available)


def choose(payload):
    for layout in candidates(len(payload)):
        try: padded_data(payload, layout)
        except ValueError: continue
        return layout
    raise ValueError('no supported layout fits payload')


def encode_final_with_layout(payload, layout):
    if not 0 < len(payload) <= PAYLOAD: raise ValueError('invalid final-page payload length')
    if (layout.generator not in GENERATORS or not 65 <= layout.lanes <= 255
            or layout.lanes % 2 != 1
            or not layout.degree < layout.words <= (1 << layout.degree)-1
            or (layout.lanes != 65 and layout.words != (1 << layout.degree)-1)):
        raise ValueError('unsupported final-page layout')
    value = padded_data(payload, layout)
    value |= parity(value, layout.lanes, layout.words-layout.degree, layout.generator) << layout.data_bits
    return value.to_bytes(layout.size, 'little')


def encode_final(payload):
    return encode_final_with_layout(payload, choose(payload))


def unpack(raw, layout):
    value = int.from_bytes(raw, 'little') & ((1 << layout.data_bits)-1)
    available = layout.data_bits-layout.footer_bits
    padding = value >> available
    if padding % 8: raise ValueError('padding length must be a whole number of bytes')
    length = (available+7)//8-padding//8
    if length <= 0: raise ValueError('invalid payload length')
    body = value & ((1 << available)-1)
    if body >> (length*8): raise ValueError('nonzero padding before footer')
    return body.to_bytes(length, 'little')


def decode_final(raw):
    canonical, alternatives = [], []
    for hit in identify(raw):
        layout = Layout(hit['lanes'], hit['codeword_bits'], int(hit['generator'], 16))
        try:
            data = unpack(raw, layout)
            if encode_final_with_layout(data, layout) != raw: continue
            alternatives.append(data)
            if choose(data) == layout: canonical.append(data)
        except ValueError: pass
    # Preserve the documented encoder policy for degenerate all-zero pages.
    # Otherwise accept only a unique parity/framing interpretation, not a
    # guessed canonical re-encoding of a historical layout.
    matches = canonical if canonical else alternatives
    if len(matches) != 1: raise ValueError('invalid, ambiguous, or unsupported final-page framing')
    return matches[0]


def encode(data):
    out = bytearray()
    for start in range(0, len(data), PAYLOAD):
        block = data[start:start+PAYLOAD]
        if len(block) == PAYLOAD: out.extend(block+trailer(block))
        else: out.extend(encode_final(block))
    return bytes(out)


def decode(raw):
    full = len(raw)//STORED
    out = bytearray()
    for i in range(full):
        page = raw[i*STORED:(i+1)*STORED]
        if trailer(page[:PAYLOAD]) == page[PAYLOAD:]:
            out.extend(page[:PAYLOAD])
        elif (i+1)*STORED == len(raw):
            out.extend(decode_final(page))
        else:
            raise ValueError(f'invalid parity or full-page padding length on page {i}')
    if raw[full*STORED:]: out.extend(decode_final(raw[full*STORED:]))
    return bytes(out)
