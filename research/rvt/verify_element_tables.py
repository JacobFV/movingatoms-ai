"""Audit project element tables and partition membership in licensed fixtures.

Reports undeclared base objects without interpreting them as live/deleted.
GUID-keyed content IDs are kept separate from project IDs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import zlib
import olefile
from codec import decode as unpage
from element_table import decode, encode, validate
from partition_segments import decode as partition_decode
from partition_objects import validate as object_validate
from episode_experiment import episodes


def inflate(payload):
    d = zlib.decompressobj(31)
    result = d.decompress(payload[8:])
    if not d.eof or d.unused_data or d.unconsumed_tail:
        raise ValueError('unexpected global stream gzip framing')
    return result


def verify(paths):
    reports = []
    for path in paths:
        with olefile.OleFileIO(path) as f:
            partitions = [(parts, partition_decode(unpage(f.openstream(parts).read())))
                          for parts in f.listdir() if parts[0] == 'Partitions']
            widths = {4 if p.root_tag == 0x365 else 8 for _, p in partitions}
            if len(widths) != 1:
                raise ValueError('missing or inconsistent partition profiles')
            width = widths.pop()
            raw = inflate(unpage(f.openstream('Global/ElemTable').read()))
            table = decode(raw, width)
            if encode(table) != raw:
                raise ValueError('element table did not round trip')
            stats = validate(table)
            ids = {table.current(row) for row in table.rows}
            history_decoder = zlib.decompressobj(31)
            history = history_decoder.decompress(unpage(f.openstream('Global/History').read())[8:])
            if not history_decoder.eof or history_decoder.unconsumed_tail:
                raise ValueError('incomplete History gzip member')
            episode_count = len(episodes(history)[2])
            episode_numbers = {table.episode(row) for row in table.rows}
            if any(n >= episode_count for n in episode_numbers):
                raise ValueError('table episode is absent from History')
            base = set()
            content = set()
            groups = []
            for parts, partition in partitions:
                for i, segment in enumerate(partition.segments):
                    objects = object_validate(segment, width)
                    found = {r.element_id for r in objects[101][:-1]}
                    (base if segment.guid is None else content).update(found)
                    groups.append({'stream': '/'.join(parts), 'group': i,
                                   'content_key': segment.guid.hex() if segment.guid else None,
                                   'ids': len(found), 'not_in_project_table': len(found-ids)})
            if ids-base:
                raise ValueError('project IDs missing from base object groups')
            reports.append({'file': path.name,
                            'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                            'id_width': width, 'table_tag': table.tag,
                            'identifier_source_tag': int.from_bytes(table.trailer[8:10], 'little'),
                            'byte_identical_round_trip': True, **stats,
                            'history_episode_count': episode_count,
                            'history_opaque_suffix_bytes': len(history_decoder.unused_data),
                            'table_episode_numbers': sorted(episode_numbers),
                            'episode_numbers_outside_zero_based_history': sorted(n for n in episode_numbers if n >= episode_count),
                            'base_object_union': len(base), 'base_objects_not_in_table': len(base-ids),
                            'table_ids_missing_base_objects': len(ids-base),
                            'content_object_union': len(content),
                            'content_ids_in_project_table': len(content & ids), 'groups': groups})
    return reports


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('files', type=Path, nargs='+')
    print(json.dumps(verify(p.parse_args().files), indent=2))
