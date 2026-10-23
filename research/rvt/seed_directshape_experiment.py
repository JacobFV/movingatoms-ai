"""Saved DirectShape mesh control with explicit lifecycle hypotheses.

Uses the public reader's saved-scene extractor, whose path supports GPolyMesh;
its ordinary IFC exporter does not map DirectShape and is not used as an oracle.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
import tempfile
import uuid
import zlib
import olefile
from codec import decode as unpage
from save_candidate import unpack_global
from schema_probe import REV
from wall_batch_experiment import code_snapshot, digest, publish_checked, write_json

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def triangle_key(points):
    """Preserve orientation while ignoring cyclic index rotation."""
    p = tuple(tuple(v) for v in points)
    return min(p, p[1:] + p[:1], p[2:] + p[:2])


def verify_scene(result, ident, points, triangles, config, allowed_positive_ids):
    scene = result['scene']
    if scene['units'] != 'feet' or scene['coordinate_frame'] != 'document Z-up':
        raise ValueError('saved-scene coordinate convention differs')
    if any(s['current_records_outside_route'] for s in [result['summary'], *scene['summaries']]):
        raise ValueError('off-route records used')
    if len(scene['elements']) != 1 or scene['elements'][0]['id'] != ident:
        raise ValueError('saved-scene owner inventory differs')
    owner = scene['elements'][0]
    meshes = owner['meshes']
    if owner['status'] != 'decoded_saved_graphics' or owner['unresolved_material_primitives']:
        raise ValueError('partial graphics or unresolved materials')
    for name in ('diagnostics', 'unbounded_faces', 'empty_trim_faces', 'rejected_filters',
                 'excluded_visibility_branches', 'excluded_non_surface_branches'):
        if meshes[name]:
            raise ValueError('saved-scene omission/diagnostic: ' + name)
    if len(meshes['primitives']) != 1:
        raise ValueError('expected one saved mesh primitive')
    primitive = meshes['primitives'][0]
    # The public traversal uses None for geometry in the selected owner's own
    # graph; source_owner_id is populated only when following a shared symbol.
    if primitive['source_owner_id'] is not None or owner['referenced_graph_sources']:
        raise ValueError('unexpected shared-symbol geometry instead of owner-local mesh')
    quantized = [[struct.unpack('<f', struct.pack('<f', v))[0] for v in p] for p in points]
    expected = Counter(triangle_key([quantized[i] for i in t]) for t in triangles)
    actual = Counter(triangle_key([primitive['vertices'][i] for i in t]) for t in primitive['triangles'])
    if actual != expected:
        raise ValueError('independent rendered triangles differ from quantized requested geometry')
    if len(primitive['normals']) != len(primitive['vertices']):
        raise ValueError('rendered normal cardinality differs')
    for n in primitive['normals']:
        if len(n) != 3 or not all(math.isfinite(v) for v in n) or abs(sum(v*v for v in n)-1) > 1e-6:
            raise ValueError('non-unit rendered normal')
    records = {r['channel']: r for r in result['records']}
    if len(result['records']) != 3 or set(records) != {101, 102, 103}:
        raise ValueError('native channel inventory differs')
    for r in records.values():
        if r['identity']['element_id'] != ident or r['source']['stream'] != 'Partitions/1':
            raise ValueError('unexpected native identity or partition')
        if not r['graph'] or r['graph']['consumed_bytes'] != r['source']['body_bytes']:
            raise ValueError('incomplete native graph')
    if records[102]['graph']['objects'][0]['class_name'] != 'DirectShape':
        raise ValueError('wrong native element class')
    objects = records[102]['graph']['objects']
    if objects[0]['fields']['m_id']['m_id']['m_id64'] != ident:
        raise ValueError('semantic root identity differs')
    metadata = [o['fields'] for o in objects if o['class_name'] == 'DirectShapeDataCell']
    expected_metadata = {'m_appGUID': config['application_id'], 'm_appDataGUID': config['application_data_id'],
                         'm_name': config['name'], 'm_categoryId': {'m_id': {'m_id64': config['category_id']}}}
    if metadata != [expected_metadata] or objects[0]['fields']['m_options'] != config['options']:
        raise ValueError('application metadata/category or explicit options differ')
    references = set()
    def visit(value):
        if isinstance(value, dict):
            for k, v in value.items():
                if k == 'm_id64' and type(v) is int and v > 0:
                    references.add(v)
                visit(v)
        elif isinstance(value, list):
            for v in value:
                visit(v)
    for record in records.values():
        visit([o['fields'] for o in record['graph']['objects']])
    if not references <= allowed_positive_ids:
        raise ValueError('unresolved positive native references')
    if records[103]['graph']['objects'][0]['fields']['m_elementId'] != ident:
        raise ValueError('graphics root owner differs')
    bounds = [[min(p[i] for p in quantized) for i in range(3)],
              [max(p[i] for p in quantized) for i in range(3)]]
    header_objects = records[101]['graph']['objects']
    outlines = [o['fields']['m_minmax'] for o in header_objects if o['class_name'] == 'Outline']
    if outlines != [bounds]:
        raise ValueError('saved header bounds differ from requested mesh')
    for channel in (102, 103):
        channel_objects = records[channel]['graph']['objects']
        roots = [o['fields'] for o in channel_objects if o['class_name'] == 'GElement']
        topologies = [o['fields'] for o in channel_objects if o['class_name'] == 'FacetedTopology0']
        polymeshes = [o['fields'] for o in channel_objects if o['class_name'] == 'GPolyMesh']
        if len(roots) != 1 or roots[0]['m_elementId'] != ident or roots[0]['m_bBox'] != bounds or roots[0]['m_tightbBox'] != bounds:
            raise ValueError('native body graphics identity/bounds differ')
        if len(topologies) != 1 or topologies[0]['m_pointsArr'] != quantized or topologies[0]['m_facetsArr'] != triangles:
            raise ValueError('native shape/display topology differs from request')
        if len(polymeshes) != 1 or polymeshes[0]['m_interiorGStyleID']['m_id']['m_id64'] != config['interior_style_id']:
            raise ValueError('native shape/display style differs')
    return {'new_element_id': ident, 'native_channels_complete': True,
            'rendered_triangles_match_request_after_float32': True,
            'rendered_triangle_count': sum(actual.values()), 'rendered_vertices': len(primitive['vertices']),
            'positive_references_resolved': sorted(references), 'application_metadata_matches': True,
            'render_materials': owner['render_materials'], 'saved_scene_status': owner['status']}


def run(source, output, reader, target, writer, *, acknowledge_hypotheses=False):
    if not acknowledge_hypotheses:
        raise ValueError('explicit current DirectShape and unchanged-Global hypotheses acknowledgment required')
    from directshape_current import construct
    from native_mesh import cuboid
    from seed_record_candidate import make
    from seed_save_context import SOURCE_SHA
    from seed_metadata_audit import run as audit
    source, output, reader, target, writer = (p.resolve() for p in (source, output, reader, target, writer))
    if output.exists():
        raise FileExistsError(output)
    if digest(source) != SOURCE_SHA:
        raise ValueError('pinned minimal seed required')
    if subprocess.check_output(['git', '-C', str(reader), 'rev-parse', 'HEAD'], text=True).strip() != REV:
        raise ValueError('reader revision differs')
    subprocess.run(['git', '-C', str(reader), 'diff', '--exit-code', 'HEAD', '--', 'src', 'Cargo.toml', 'Cargo.lock'], check=True)
    paths = {n: HERE / 'results' / n for n in ('directshape-mesh-profile.json', 'directshape_legacy_audit.json', 'directshape_legacy_global.json', 'seed_save_context.json')}
    raws = {n: p.read_bytes() for n, p in paths.items()}
    profiles = {n: json.loads(b) for n, b in raws.items()}
    code = code_snapshot()
    output.mkdir(parents=True, exist_ok=False)
    report = {'status': 'running', 'started_at_utc': datetime.now(timezone.utc).isoformat(),
              'source_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
              'source_sha256': digest(source), 'code_sha256': code, 'writer_sha256': digest(writer),
              'profile_sha256': {n: hashlib.sha256(b).hexdigest() for n, b in raws.items()},
              'autodesk_acceptance': 'not_tested', 'production_native_export': False}
    write_json(output / 'run.json', report)
    try:
        with tempfile.TemporaryDirectory(dir=output) as temporary:
            work = Path(temporary)
            (work / 'src').mkdir()
            (work / 'src/main.rs').write_bytes((HERE / 'seed_directshape_probe.rs').read_bytes())
            (work / 'Cargo.toml').write_text('[package]\nname="rvt-seed-directshape-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path=' + json.dumps(str(reader)) + '}\nserde_json="=1.0.154"\n')
            subprocess.run(['cargo', 'build', '--release', '--offline', '--manifest-path', str(work / 'Cargo.toml'), '--target-dir', str(target)], check=True)
            probe = target / 'release/rvt-seed-directshape-probe'
            with olefile.OleFileIO(source) as f:
                schema = zlib.decompress(unpage(f.openstream('Formats/Latest').read()), 31)
                original_global = unpack_global(unpage(f.openstream('Global/Latest').read()))[0]
                from wall_batch_metadata_audit import table_parts, inflate_global
                _, table_rows, _, _ = table_parts(inflate_global(f.openstream('Global/ElemTable').read()))
                allowed_positive_ids = {struct.unpack_from('<Q', row, 20)[0] for row in table_rows} | {2746}
            (work / 'schema.bin').write_bytes(schema)
            declarations = json.loads(subprocess.check_output([str(probe), 'schema', str(work / 'schema.bin')]))
            legacy = profiles['directshape_legacy_audit.json']
            legacy_root = next(r for r in legacy['records'] if r['channel'] == 102)['representatives']['DirectShape']['fields']
            config = {'category_id': -2000011, 'style_id': 119, 'interior_style_id': 125, 'header_flags': 8488, 'can_create_parts_status': 0,
                      'application_id': '82c29ad8-927c-49a8-9c1a-726eae1f745b', 'application_data_id': 'movingatoms-research-mesh-001', 'name': 'Moving Atoms research mesh',
                      'options': {'m_PresentationType': 0, 'm_ReferencingOption': 0, 'm_RoomBoundingOption': 0,
                                  'm_AllowsChangeTypeId': False, 'm_AllowsCopy': True, 'm_AllowsLock': False, 'm_AllowsMove': True, 'm_AllowsTagAlongCurve': False}}
            points, triangles = cuboid()
            bodies, graphs, construction = construct(declarations, profiles['directshape-mesh-profile.json'], legacy_root, 2746,
                                                      points, triangles, config, acknowledge_hypotheses=True)
            request = {'element_id': 2746, 'units': 'feet', 'vertices': points, 'triangles': triangles, 'config': config}
            write_json(output / 'request.json', request)
            write_json(output / 'construction.json', construction)
            registration = {'source_sha256': SOURCE_SHA, 'source_global_sha256': hashlib.sha256(original_global).hexdigest(),
                            'registered_global_sha256': hashlib.sha256(original_global).hexdigest(), 'changes': [],
                            'method': 'Explicit no-Global-membership hypothesis from historical 2015 DirectShape instance audit; current-version lifecycle unvalidated',
                            'historical_evidence_sha256': report['profile_sha256']['directshape_legacy_global.json']}
            guid = uuid.uuid5(uuid.UUID('22072303-bb24-56dd-ae91-329cbdbe7a7e'), json.dumps(request, sort_keys=True))
            make(source, output / 'patches', [{'id': 2746, 'bodies': bodies}], profiles['seed_save_context.json'], original_global,
                 registration, episode_guid=str(guid), timestamp=1792627200, acknowledge_hypotheses=True)
            candidate = output / 'candidate.rvt'
            writer_result = subprocess.check_output([str(writer), 'patch', str(source), str(candidate), str(output / 'patches/manifest.json')])
            (output / 'transport.json').write_bytes(writer_result)
            metadata = audit(source, candidate, expected_global_change=False)
            write_json(output / 'metadata.json', metadata)
            actual = json.loads(subprocess.check_output([str(probe), str(candidate), '2746']))
            write_json(output / 'scene.json', actual)
            checked = verify_scene(actual, 2746, points, triangles, config, allowed_positive_ids)
            checked.update(candidate_sha256=digest(candidate), probe_binary_sha256=digest(probe), reader_revision=REV,
                           saved_scene_sha256=digest(output / 'scene.json'), autodesk_acceptance='not_tested')
            write_json(output / 'native.json', checked)
            if code_snapshot() != code or any(p.read_bytes() != raws[n] for n, p in paths.items()) or digest(writer) != report['writer_sha256'] or digest(source) != SOURCE_SHA:
                raise ValueError('code, source evidence or tool changed during verification')
            candidate_sha = publish_checked(candidate, output / 'verified-candidate.rvt', [metadata, checked])
            report.update(status='verified_research_candidate', candidate_sha256=candidate_sha,
                          validation_reports={n: digest(output / n) for n in ('metadata.json', 'native.json', 'scene.json')},
                          native_application_acceptance=False, complete_save_transaction=False,
                          completed_at_utc=datetime.now(timezone.utc).isoformat())
            write_json(output / 'run.json', report)
            return report
    except Exception as exc:
        report.update(status='failed', error=f'{type(exc).__name__}: {exc}', completed_at_utc=datetime.now(timezone.utc).isoformat())
        write_json(output / 'run.json', report)
        raise


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('output', type=Path)
    p.add_argument('--reader', type=Path, required=True)
    p.add_argument('--target', type=Path, default=HERE / 'local/seed-wall-verify-build')
    p.add_argument('--writer', type=Path, default=ROOT / 'processing/rvt-native/target/release/ma-rvt-native')
    p.add_argument('--acknowledge-hypotheses', action='store_true')
    a = p.parse_args()
    result = run(a.source, a.output, a.reader, a.target, a.writer, acknowledge_hypotheses=a.acknowledge_hypotheses)
    print(json.dumps({k: result[k] for k in ('status', 'candidate_sha256')}, indent=2))
