"""Re-encode a measured GPolyMesh-bearing record from complete schema fields.

This reproduces SiteSurface records; it does not claim to author DirectShape
instances or a standalone RVT document. No opaque body copying is used.
"""
import argparse
import hashlib
import json
from pathlib import Path
from wall_element import GraphEncoder


def declarations_for(graph, declarations):
    classes = {c['tag']: c for c in declarations}
    needed = set()
    def collect(value):
        if isinstance(value, dict):
            if value.get('class_tag') is not None:
                needed.add(value['class_tag'])
            for child in value.values(): collect(child)
        elif isinstance(value, list):
            for child in value: collect(child)
    collect(graph)
    def refs(field):
        for ref in field['references']: needed.add(ref['tag'])
        if field['nested_descriptor']: refs(field['nested_descriptor'])
    previous = None
    while previous != needed:
        previous = set(needed)
        for tag in previous:
            cls = classes[tag]
            parent = cls['parent_reference']['tag']
            if parent: needed.add(parent)
            for field in cls['fields']: refs(field)
    return [classes[tag] for tag in sorted(needed)]


def encode_profile(profile):
    if profile['scope'] != 'source-exact SiteSurface GPolyMesh records':
        raise ValueError('unsupported profile scope')
    output = {}
    for record in profile['records']:
        if record['status'] != 'complete_bounded_graph':
            raise ValueError('incomplete source graph')
        body = GraphEncoder(record['declarations']).graph(record['graph'])
        if len(body) != record['source']['body_bytes'] or hashlib.sha256(body).hexdigest() != record['source']['body_sha256']:
            raise ValueError('source-exact re-encoding differs')
        output[record['channel']] = body
    if set(output) != {101, 102, 103}: raise ValueError('all channels required')
    return output


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('profile', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    bodies = encode_profile(json.loads(args.profile.read_text()))
    if args.output:
        args.output.mkdir(parents=True, exist_ok=False)
        for channel, body in bodies.items():
            (args.output / f'{channel}.bin').write_bytes(body)
    print(json.dumps({str(c): {'bytes': len(b), 'sha256': hashlib.sha256(b).hexdigest()} for c,b in bodies.items()}, indent=2))
