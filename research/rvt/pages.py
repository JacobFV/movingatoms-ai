"""Byte-only RVT page observations; no Autodesk/ODA implementation sources."""
from dataclasses import dataclass
import hashlib
from pathlib import Path

STORED = 65249
PAYLOAD = 64896
CORE_SHA256 = 'c805df445d613b408e37337765572021265e3f5dfdc7d1fa53b22ba1600b8014'
GLOBAL = {'ContentDocuments', 'DocumentIncrementTable', 'ElemTable', 'History', 'Latest', 'PartitionTable'}

def is_paged(parts):
    return parts == ['Contents'] or (len(parts) == 2 and (
        parts[0] == 'Partitions' or
        parts[0] == 'Global' and parts[1] in GLOBAL or
        parts == ['Formats', 'Latest']))


@dataclass(frozen=True)
class Page:
    stream: str
    index: int
    data: bytes

    @property
    def payload(self):
        return self.data[:PAYLOAD]

    @property
    def trailer(self):
        return self.data[PAYLOAD:]


def read_pages(path):
    import olefile
    with olefile.OleFileIO(path) as ole:
        for parts in ole.listdir():
            if not is_paged(parts):
                continue
            stream = '/'.join(parts)
            data = ole.openstream(parts).read()
            for i in range(len(data) // STORED):
                yield Page(stream, i, data[i * STORED:(i + 1) * STORED])


def audit(path):
    """Exact GF(2) elimination, using every payload bit, with trailer targets.

    Independent input rows cannot test linearity. Only dependent rows supply
    constraints; report that explicitly instead of treating a fit as evidence.
    """
    basis = {}
    contradictions = []
    dependencies = 0
    streams = {}
    constants = None
    pages = list(read_pages(path))
    for p in pages:
        streams[p.stream] = streams.get(p.stream, 0) + 1
        if constants is None:
            constants = dict(enumerate(p.trailer))
        constants = {i: v for i, v in constants.items() if p.trailer[i] == v}
        x, y = int.from_bytes(p.payload, 'little'), int.from_bytes(p.trailer, 'little')
        while x:
            pivot = x.bit_length()
            if pivot not in basis:
                basis[pivot] = (x, y)
                break
            bx, by = basis[pivot]
            x ^= bx
            y ^= by
        if not x:
            dependencies += 1
            if y:
                contradictions.append({'stream': p.stream, 'page': p.index})
    return {'file_sha256': hashlib.sha256(Path(path).read_bytes()).hexdigest(),
            'stored_page_bytes': STORED, 'payload_bytes': PAYLOAD,
            'full_pages': len(pages), 'streams': streams,
            'constant_trailer_bytes': constants, 'payload_bit_rank': len(basis),
            'dependent_rows': dependencies, 'linear_contradictions': contradictions,
            'linearity_verdict': ('rejected_for_this_framing' if contradictions else
                'underdetermined' if not dependencies else 'consistent_not_proven')}

if __name__ == '__main__':
    import argparse, json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('file')
    parser.add_argument('--export', type=Path, help='Export raw pages for ECC probe')
    args = parser.parse_args()
    if args.export:
        args.export.write_bytes(b''.join(p.data for p in read_pages(args.file)))
    print(json.dumps(audit(args.file), indent=2))
