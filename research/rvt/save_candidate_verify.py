"""Verify append candidate with independent current routing and full graphs."""
import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import tempfile
import re
from collections import Counter
from verify_resized_graph import verify as verify_graph
from validation_bundle import canonical_ifc


def verify(directory, stem="save-candidate"):
    evidence = directory/(stem+'-native.json')
    rows = json.loads(evidence.read_bytes())
    if len(rows) != 2: raise ValueError('expected source/candidate native evidence')
    from parameter_experiment import SOURCE_SHA
    from schema_probe import REV
    for row, filename in zip(rows, ('RE1-Architecture.rvt', stem+'.rvt')):
        digest = hashlib.sha256((directory/filename).read_bytes()).hexdigest()
        if row['sha256'] != digest or row['file'] != filename or row['reader_commit'] != REV:
            raise ValueError('native evidence does not match current files and pinned reader')
    if rows[0]['sha256'] != SOURCE_SHA: raise ValueError('source is not pinned fixture')
    before, after = [r['record'] for r in rows]
    if any(r['status'] != 'complete_bounded_graph' for r in (before,after)):
        raise ValueError('incomplete native graph')
    if before['source']['stream'] != 'Partitions/80' or after['source']['stream'] != 'Partitions/85':
        raise ValueError('unexpected current-record route')
    expected = deepcopy(before['identity']); expected['stored_revision'] = 703; expected['raw_fields'][3] = 703
    if expected != after['identity']: raise ValueError('unexpected identity change')
    if before['derived_default_ifc_guid'] != after['derived_default_ifc_guid']:
        raise ValueError('derived IFC identity changed')
    with tempfile.TemporaryDirectory() as temp:
        path = Path(temp)/'graphs.json'
        path.write_text(json.dumps([{'graph':r['record']['graph'],'reader_commit':r['reader_commit']} for r in rows]))
        graph = verify_graph(path)
    expected = json.loads((directory/'architecture-elements.json').read_bytes())
    actual = json.loads((directory/(stem+'-elements.json')).read_bytes())
    fields = [f for e in expected if e['id'] == 348738 for f in e['fields'] if f['name'] == 'm_room_floor_finish']
    if len(fields) != 1 or fields[0]['value'] != 'Wood': raise ValueError('source reader property differs')
    fields[0]['value'] = 'Polished concrete'
    room = next(e for e in expected if e['id'] == 348738)
    if room['byte_range'] != {'start':242983,'end':243119}: raise ValueError('unexpected original location')
    room['byte_range'] = {'start':0,'end':136}
    room['provenance']['source_offset'] = 0; room['provenance']['source_stream'] = 'Partitions/85'
    for field in room['fields']:
        if field['name'] == 'm_source_offset': field['value'] = 0
        if field['name'] == 'm_source_stream': field['value'] = 'Partitions/85'
    if expected != actual: raise ValueError('legacy reader projection differs beyond room property')
    left = canonical_ifc((directory/'architecture-original.ifc').read_bytes()).splitlines()
    right = canonical_ifc((directory/(stem+'.ifc')).read_bytes()).splitlines()
    changes = [(a,b) for a,b in zip(left,right) if a != b]
    if len(left) != len(right): raise ValueError('IFC line count changed')
    guid_pattern = re.compile(rb"^(#\d+=([A-Z0-9]+)\(')([0-3][0-9A-Za-z_$]{21})('.*)$")
    identifier_changes = Counter(); other_changes = []
    for a,b in changes:
        old,new = guid_pattern.match(a),guid_pattern.match(b)
        if old and new and old[1] == new[1] and old[4] == new[4]:
            identifier_changes[old[2].decode()] += 1
        else: other_changes.append((a,b))
    if len(other_changes) != 2: raise ValueError('unexpected IFC non-identifier changes')
    expected_changes = [
        (b"IFCTEXT('Partitions/80')", b"IFCTEXT('Partitions/85')"),
        (b"IFCLABEL('Wood')", b"IFCLABEL('Polished concrete')")]
    for (a,b), (old,new) in zip(other_changes, expected_changes):
        if old not in a or b != a.replace(old,new): raise ValueError('unexpected IFC property/provenance change')
    return {'candidate_sha256': hashlib.sha256((directory/(stem+'.rvt')).read_bytes()).hexdigest(),
            'native_evidence_sha256': hashlib.sha256(evidence.read_bytes()).hexdigest(),
            'current_record_before':before['source']['stream'], 'current_record_after':after['source']['stream'],
            'unique_id_unchanged':True,'derived_ifc_guid_unchanged':True,
            'full_graph':graph, 'reader_element_count':len(actual),
            'reader_only_expected_property_and_source_location_changes':True,'ifc_non_identifier_changes_are_expected_property_and_source_stream':True,
            'ifc_total_changed_lines':len(changes), 'ifc_identifier_only_changes':dict(identifier_changes),
            'ifc_identifiers_stable':not identifier_changes,
            'autodesk_acceptance':'not_tested','complete_save_transaction':False}

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path)
    p.add_argument('--stem', default='save-candidate')
    a=p.parse_args(); print(json.dumps(verify(a.directory,a.stem),indent=2))
