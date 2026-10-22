"""Pinned-fixture episode-list experiment with proper framing and page parity.

Not a complete Revit save transaction. Save-counter/other bookkeeping is not
changed, and Revit acceptance is untested. Wire facts are independently checked
against the fixture and the public rvt-rs revit_global_ids.rs parser at b6086d4:
count at 0x0e; skipped-u32 table at 0x66; second count; GUID+0x28 entries,
newest first. No Autodesk/ODA implementation sources are used.
"""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import uuid
import zlib
from pages import CORE_SHA256
from partial_pages import identify, parity


def episodes(data):
    count = struct.unpack_from('<I', data, 14)[0]
    skipped = struct.unpack_from('<I', data, 102)[0]
    count_at = 106+4*skipped
    if count != struct.unpack_from('<I', data, count_at)[0]:
        raise ValueError('episode counts disagree')
    start = count_at+4
    end = start+17*count
    if end > len(data): raise ValueError('episode table truncated')
    entries = [data[i:i+17] for i in range(start, end, 17)]
    if any(e[-1] != 0x28 for e in entries): raise ValueError('invalid episode terminator')
    return count_at, start, entries


def prepend(data, guid):
    if len(guid) != 16: raise ValueError("GUID must be 16 bytes")
    count_at, start, entries = episodes(data)
    if guid in [e[:16] for e in entries]: raise ValueError('episode GUID already exists')
    out = bytearray(data[:start] + guid+b'\x28' + data[start:])
    for offset in (14, count_at): struct.pack_into('<I', out, offset, len(entries)+1)
    _, _, changed = episodes(out)
    if changed[1:] != entries: raise ValueError('existing episode mapping changed')
    return bytes(out)


def make(input_path, output_dir, guid):
    import olefile
    source = input_path.read_bytes()
    if hashlib.sha256(source).hexdigest() != CORE_SHA256:
        raise ValueError('experiment accepts only the pinned licensed Core Interior fixture')
    with olefile.OleFileIO(input_path) as f: raw = f.openstream('Global/History').read()
    layouts = identify(raw)
    if len(layouts) != 1: raise ValueError('no unique final-page layout')
    layout = layouts[0]
    if layout['data_bits'] % 8: raise ValueError('fixture history data must be byte-aligned')
    original = raw[:layout['data_bits']//8]
    if original[8:12] != b'\x1f\x8b\x08\x00': raise ValueError('unexpected gzip framing')
    decoder = zlib.decompressobj(31)
    old = decoder.decompress(original[8:])
    if not decoder.eof: raise ValueError('incomplete gzip member')
    new = prepend(old, guid.bytes_le)
    compressor = zlib.compressobj(9, zlib.DEFLATED, -15)
    compressed = (original[8:18] + compressor.compress(new) + compressor.flush() +
                  struct.pack('<II', zlib.crc32(new), len(new)))
    if zlib.decompress(compressed, 31) != new: raise ValueError('gzip verification failed')
    logical = original[:8] + compressed + decoder.unused_data
    lanes = layout['lanes']
    gen = int(layout['generator'], 16)
    degree = gen.bit_length()-1
    words = (len(logical)*8+lanes-1)//lanes
    if words+degree >= 1 << degree:
        raise ValueError('new history exceeds this experimental layout')
    data_bits = words*lanes
    data = int.from_bytes(logical, 'little')
    stored_int = data | parity(data, lanes, words, gen) << data_bits
    stored = stored_int.to_bytes(((words+degree)*lanes+7)//8, 'little')
    detected = identify(stored)
    if len(detected) != 1 or detected[0]['data_bits'] != data_bits:
        raise ValueError('new final-page layout did not verify uniquely')
    output_dir.mkdir(parents=True, exist_ok=False)
    (output_dir/'history.bin').write_bytes(stored)
    manifest = {'input_sha256': CORE_SHA256, 'patches': [{
        'stream': 'Global/History', 'expected_stored_sha256': hashlib.sha256(raw).hexdigest(),
        'new_unpaged_file': 'history.bin'}]}
    (output_dir/'manifest.json').write_text(json.dumps(manifest, indent=2)+'\n')
    return {'input_sha256': CORE_SHA256, 'episode_count_before': len(episodes(old)[2]),
        'episode_count_after': len(episodes(new)[2]), 'new_episode_guid': str(guid),
        'existing_episode_number_to_guid_mapping_preserved': True,
        'prefix_hex_preserved': original[:8].hex(),
        'opaque_data_suffix_bytes_preserved': len(decoder.unused_data),
        'stored_bytes_before': len(raw), 'stored_bytes_after': len(stored),
        'new_final_page_layout': detected[0], 'complete_revit_transaction': False,
        'save_counter_modified': False, 'revit_openability': 'not_tested'}

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('input', type=Path)
    p.add_argument('output_dir', type=Path)
    p.add_argument('--guid', type=uuid.UUID, required=True)
    args = p.parse_args()
    print(json.dumps(make(args.input, args.output_dir, args.guid), indent=2))
