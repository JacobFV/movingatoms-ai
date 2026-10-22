"""Static-file audit of creation, modification and user-modification episodes."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import subprocess
import tempfile
import zlib
import uuid
from save_history import decode as history_decode, encode as history_encode, prepend_episode
import olefile
from codec import decode as unpage
from partition_segments import decode as partition
from partition_objects import validate
from schema_probe import REV

RUST = r'''
fn main() {
 let args: Vec<String> = std::env::args().collect();
 let dir = std::path::Path::new(&args[1]);
 let read = |n| std::fs::read(dir.join(n)).unwrap();
 let registry = rvt::schema_registry::parse(&read("schema.bin")).unwrap();
 let history = read("history.bin"); let table = read("table.bin");
 let episodes = rvt::native_index::creation_episodes(&history, &registry).unwrap();
 let index = rvt::native_index::parse(&table, &registry, &episodes).unwrap();
 let tag = u16::from_le_bytes(table[..2].try_into().unwrap());
 let rowtag = registry.class(tag).unwrap().fields[0].references[0].tag;
 let firstrow = rvt::native_parameters::decode_object_fields(&table, &registry, 6, rowtag).unwrap();
 let records = read("record.bin");
 let recordtag = u16::from_le_bytes(records[..2].try_into().unwrap());
 let object = rvt::native_parameters::decode_object_fields(&records, &registry, 2, recordtag);
 let object_json = match object {
    Ok(decoded) => serde_json::json!({"decoded": decoded}),
    Err(error) => serde_json::json!({"error": error.to_string()})
 };
 println!("{}", serde_json::json!({"identities": index.identities, "row_stride": index.row_stride,
   "first_row": firstrow, "record_class": registry.class(recordtag).unwrap().name,
   "record": object_json, "episode_count": episodes.len()}));
}
'''


def relationships(rows, episodes):
    counts = Counter(); out_of_range = []; outside_values = Counter()
    for r in rows:
        c, m, u = r['creation_episode'], r['stored_revision'], r['other_revision']
        counts['all_equal' if c == m == u else 'creation_equals_user_below_modification'
               if c == u < m else 'creation_below_user_equals_modification' if c < u == m
               else 'creation_below_user_below_modification' if c < u < m else 'other'] += 1
        if any(x >= episodes for x in (c, m, u)):
            out_of_range.append(r['element_id'])
            for name, value in zip(('creation', 'modification', 'user_modification'), (c,m,u)):
                if value >= episodes: outside_values[(name,value)] += 1
    return {'relationship_counts': dict(sorted(counts.items())), 'out_of_history_ids': out_of_range,
            'out_of_history_values': [{'field':k[0], 'value':k[1], 'count':v}
                                      for k,v in sorted(outside_values.items())]}


def audit(source, target, evidence, directory):
    source, target = source.resolve(), target.resolve()
    if subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip() != REV:
        raise ValueError('reader revision mismatch')
    subprocess.run(['git', '-C', str(source), 'diff', '--exit-code', 'HEAD', '--', 'src', 'Cargo.toml', 'Cargo.lock'], check=True)
    reports=[]
    with tempfile.TemporaryDirectory(dir=directory) as tmp:
        project=Path(tmp); (project/'src').mkdir(); (project/'src/main.rs').write_text(RUST)
        (project/'Cargo.toml').write_text('[package]\nname="rvt-modification-history-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(source))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo', 'build', '--release', '--offline', '--manifest-path', str(project/'Cargo.toml'), '--target-dir', str(target)], check=True)
        for e in evidence:
            path=directory/e['file']
            if path.parent.resolve()!=directory.resolve() or hashlib.sha256(path.read_bytes()).hexdigest()!=e['sha256']:
                raise ValueError('fixture mismatch')
            with olefile.OleFileIO(path) as f:
                for name, stream, skip in [('schema','Formats/Latest',0),('history','Global/History',8),('table','Global/ElemTable',8)]:
                    compressed=unpage(f.openstream(stream).read())[skip:]; gz=zlib.decompressobj(31); data=gz.decompress(compressed)
                    if not gz.eof or gz.unconsumed_tail: raise ValueError('invalid global gzip')
                    (project/(name+'.bin')).write_bytes(data)
                sample=None
                # One representative native channel 101 record per fixture; exact IDs reported.
                for parts in f.listdir():
                    if parts[0]!='Partitions':continue
                    p=partition(unpage(f.openstream(parts).read())); width=4 if p.root_tag==0x365 else 8
                    records=validate(p.segments[0],width)[101]
                    if not records[:-1]:continue
                    choices=[r for r in records if r.element_id==348738] if path.name=='RE1-Architecture.rvt' else records[:1]
                    if choices: sample=(parts,choices[0]);break
                if sample is None: raise ValueError('no native record')
                (project/'record.bin').write_bytes(sample[1].body)
            raw=json.loads(subprocess.check_output([str(target/'release/rvt-modification-history-probe'),str(project)]))
            rows=list(raw['identities'].values())
            # Privacy: only structural fields from the first row and native sample are committed.
            spans=raw['first_row']['field_spans']
            named={name: [{'start': s['start']-6,'end': s['end']-6} for s in spans if s['name']==name]
                   for name in ('m_originalElementId','m_creationDate','m_lastModificationDate','m_lastUserModificationDate','m_id')}
            mutation_evidence = None
            room=raw['identities'].get('348738')
            if path.name == 'RE1-Architecture.rvt':
                history = history_decode((project/'history.bin').read_bytes())
                changed = prepend_episode(history, uuid.UUID('5f197eb7-5987-5937-94d9-99f5208ac16c').bytes_le)
                (project/'history.bin').write_bytes(history_encode(changed))
                table_bytes = bytearray((project/'table.bin').read_bytes())
                mutations = []
                for user_episode in (room['other_revision'], history.next_sequence):
                    struct.pack_into('<I', table_bytes, room['row_offset']+12, history.next_sequence)
                    struct.pack_into('<I', table_bytes, room['row_offset']+16, user_episode)
                    (project/'table.bin').write_bytes(table_bytes)
                    candidate = json.loads(subprocess.check_output([str(target/'release/rvt-modification-history-probe'),str(project)]))
                    expected = dict(raw['identities']['348738'], stored_revision=history.next_sequence,
                                    other_revision=user_episode)
                    expected['raw_fields'] = list(expected['raw_fields'])
                    expected['raw_fields'][3:5] = [history.next_sequence, user_episode]
                    if candidate['identities']['348738'] != expected:
                        raise ValueError('native room identity changed unexpectedly')
                    if any(candidate['identities'][k] != v for k,v in raw['identities'].items() if k != '348738'):
                        raise ValueError('unrelated native identity changed')
                    mutations.append({'modification_episode':history.next_sequence,'user_modification_episode':user_episode,
                                      'native_unique_id_unchanged':True,'unrelated_native_identities_unchanged':True})
                mutation_evidence = mutations
            if room:
                room={k:room[k] for k in ('element_id','row_offset','creation_episode','stored_revision','other_revision','unique_id')}
            native=raw['record']
            native_summary={'stream':'/'.join(sample[0]),'element_id':sample[1].element_id,
                            'class':raw['record_class'],'body_sha256':hashlib.sha256(sample[1].body).hexdigest()}
            if 'error' in native: native_summary['decode_error']=native['error']
            else:
                native_summary['decoded_field_names']=sorted(native['decoded']['fields'])
                native_summary['decoded_end']=native['decoded']['end']
                native_summary['body_bytes']=len(sample[1].body)
                native_summary['field_spans']=native['decoded']['field_spans']
                native_summary['regen_history']=native['decoded']['fields']['m_regenHistory']
            reports.append({'file':path.name,'sha256':e['sha256'],'reader_commit':REV,
                            'rows':len(rows),'episode_count':raw['episode_count'],'row_stride':raw['row_stride'],
                            'row_relative_field_spans':named,**relationships(rows,raw['episode_count']),
                            'room_identity':room,'native_channel_101_sample':native_summary,
                            'room_mutation_identity_checks':mutation_evidence})
    return reports

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reader-source',type=Path,required=True);p.add_argument('--target',type=Path,required=True)
    p.add_argument('evidence',type=Path);p.add_argument('directory',type=Path);a=p.parse_args()
    print(json.dumps(audit(a.reader_source,a.target,json.loads(a.evidence.read_bytes()),a.directory),indent=2))
