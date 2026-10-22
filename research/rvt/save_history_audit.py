"""Cross-check History codec and mutation using the pinned public schema reader."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import uuid
import zlib
import olefile
from codec import decode as unpage
from save_history import decode, encode, prepend_episode, root_fields
from schema_probe import REV

RUST = r'''
fn main() {
    let args: Vec<String> = std::env::args().collect();
    let schema = std::fs::read(&args[1]).unwrap();
    let history = std::fs::read(&args[2]).unwrap();
    let registry = rvt::schema_registry::parse(&schema).unwrap();
    let episodes = rvt::native_index::creation_episodes(&history, &registry).unwrap();
    let tag = u16::from_le_bytes(history[..2].try_into().unwrap());
    let root = rvt::native_parameters::decode_object_fields(&history, &registry, 2, tag).unwrap();
    let descriptors = &registry.named("DocumentHistory").unwrap().fields;
    let episode_tag = registry.named("Episode").unwrap().tag;
    let mut pos = root.end + 4;
    let mut episode_fields = Vec::new();
    for _ in &episodes {
        let row = rvt::native_parameters::decode_object_fields(&history, &registry, pos, episode_tag).unwrap();
        pos = row.end; episode_fields.push(row.fields);
    }
    println!("{}", serde_json::json!({"episodes": episodes, "fields": root.fields,
        "descriptors": descriptors, "episode_fields": episode_fields}));
}
'''


def audit(source, target, evidence, directory):
    source = source.resolve(); target = target.resolve()
    if subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip() != REV:
        raise ValueError('reader revision mismatch')
    subprocess.run(['git', '-C', str(source), 'diff', '--exit-code', 'HEAD', '--', 'src', 'Cargo.toml', 'Cargo.lock'], check=True)
    reports = []
    with tempfile.TemporaryDirectory(dir=directory) as tmp:
        project = Path(tmp); (project/'src').mkdir()
        (project/'src/main.rs').write_text(RUST)
        (project/'Cargo.toml').write_text('[package]\nname="rvt-save-history-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(source))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo', 'build', '--release', '--offline', '--manifest-path', str(project/'Cargo.toml'), '--target-dir', str(target)], check=True)
        for item in evidence:
            path = directory/item['file']
            if path.parent.resolve() != directory.resolve(): raise ValueError('invalid evidence filename')
            if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']: raise ValueError('fixture mismatch')
            with olefile.OleFileIO(path) as file:
                schema = zlib.decompress(unpage(file.openstream('Formats/Latest').read()), 31)
                compressed = unpage(file.openstream('Global/History').read())[8:]
                gzip = zlib.decompressobj(31); raw = gzip.decompress(compressed)
                if not gzip.eof or gzip.unconsumed_tail: raise ValueError('invalid History gzip')
            history = decode(raw)
            if encode(history) != raw: raise ValueError('History bytes do not reproduce')
            (project/'schema.bin').write_bytes(schema)
            def independent(data):
                (project/'history.bin').write_bytes(data)
                return json.loads(subprocess.check_output([str(target/'release/rvt-save-history-probe'), str(project/'schema.bin'), str(project/'history.bin')]))
            original = independent(raw)
            expected = [str(uuid.UUID(bytes_le=e[:16])) for e in history.episodes]
            descriptors = {d['name']: {'raw_descriptor': d['raw_descriptor'],
                           'base': d['base'], 'modifier': d['modifier']}
                           for d in original['descriptors'] if d['name'] in
                           ('m_nextLocalSequenceNumber', 'm_subsequenceNumberDeficit', 'm_upgradeVersions')}
            def episode_fields(h):
                return [{'m_eGUID': {'m_guid': {'m_guid': {'guid_bytes': list(e[:16])}}},
                         'm_strength': e[16]} for e in h.episodes]
            if original['episode_fields'] != episode_fields(history):
                raise ValueError('independent episode fields disagree')
            if original['episodes'] != expected or original['fields'] != root_fields(history):
                raise ValueError('independent History fields disagree')
            guid = uuid.uuid5(uuid.NAMESPACE_URL, 'rvt-clean-room-history-test:'+item['sha256'])
            changed = prepend_episode(history, guid.bytes_le)
            verified = independent(encode(changed))
            if (verified['episodes'] != [str(guid)]+expected or verified['fields'] != root_fields(changed)
                    or verified['episode_fields'] != episode_fields(changed)):
                raise ValueError('independent History mutation disagrees')
            reports.append({'file': path.name, 'sha256': item['sha256'], 'reader_commit': REV,
                            'inflated_bytes': len(raw), 'episodes': len(history.episodes),
                            'upgrade_versions': len(history.upgrade_versions),
                            'schema_root_fields_equal': True, 'schema_episode_guids_equal': True,
                            'schema_episode_fields_equal': True, 'integer_descriptors': descriptors,
                            'byte_exact_roundtrip': True, 'mutated_schema_fields_and_guids_equal': True,
                            'existing_reverse_indexed_episode_ids_preserved': True,
                            'complete_save_transaction': False})
    return reports


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--reader-source', type=Path, required=True); p.add_argument('--target', type=Path, required=True)
    p.add_argument('evidence', type=Path); p.add_argument('directory', type=Path)
    a = p.parse_args()
    print(json.dumps(audit(a.reader_source, a.target, json.loads(a.evidence.read_bytes()), a.directory), indent=2))
