"""Bind complete saved header bounds to exact/explicit-compaction selection."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
import olefile
from codec import decode as unpage
from partition_segments import decode as part_decode
from partition_objects import validate
from new_element_experiment import SOURCE_SHA
from schema_probe import REV


def run(reader,source,target,selection):
    reader=reader.resolve();target=target.resolve();source=source.resolve()
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:raise ValueError('requires pinned core2024')
    selected=next(r for r in json.loads(selection.read_bytes()) if r['sha256']==SOURCE_SHA)
    cases=selected['candidates']
    if len(cases)!=10 or any(c['selection_evidence']!='unique_compaction_history_holder' for c in cases):
        raise ValueError('requires ten explicit compaction selections')
    if subprocess.check_output(['git','-C',str(reader),'rev-parse','HEAD'],text=True).strip()!=REV:raise ValueError('reader pin differs')
    subprocess.run(['git','-C',str(reader),'diff','--exit-code','HEAD','--','src','Cargo.toml','Cargo.lock'],check=True)
    with tempfile.TemporaryDirectory(dir=Path(__file__).parent/'local') as tmp:
        work=Path(tmp);(work/'src').mkdir()
        (work/'src/main.rs').write_bytes(Path(__file__).with_name('wall_element_probe.rs').read_bytes())
        (work/'Cargo.toml').write_text('[package]\nname="rvt-wall-element-probe"\nversion="0.1.0"\nedition="2024"\n[dependencies]\nrvt={path='+json.dumps(str(reader))+'}\nserde_json="=1.0.154"\n')
        subprocess.run(['cargo','build','--release','--offline','--manifest-path',str(work/'Cargo.toml'),'--target-dir',str(target)],check=True)
        binary=target/'release/rvt-wall-element-probe'
        result=json.loads(subprocess.check_output([str(binary),'headerbounds',str(source),','.join(str(c['element']) for c in cases)]))
    summary=result['summary']
    if summary['unsupported_graph_records'] or summary['complete_graph_records']!=26425 or summary['current_records_outside_route']!=10:
        raise ValueError('incomplete or unexpected header selection')
    actual={r['element']:r['source'] for r in result['selected_source_records']}
    if set(actual)!={c['element'] for c in cases}:raise ValueError('trace IDs differ')
    audited=[]
    with olefile.OleFileIO(source) as f:
        streams={}
        for case in cases:
            stream=f"Partitions/{case['selected_increment']}"
            if stream not in streams:streams[stream]=validate(part_decode(unpage(f.openstream(stream).read())).segments[0],8)[101]
            records=[r for r in streams[stream] if r.element_id==case['element']]
            if len(records)!=1:raise ValueError('ambiguous selected header')
            digest=hashlib.sha256(records[0].body).hexdigest()
            if actual[case['element']]['stream']!=stream or actual[case['element']]['body_sha256']!=digest:
                raise ValueError('public fallback does not match explicit compaction holder')
            audited.append({**case,'stream':stream,'header_body_sha256':digest,'independent_reader_body_matches':True})
    return {'source_sha256':SOURCE_SHA,'reader_revision':REV,
        'selection_report_sha256':hashlib.sha256(selection.read_bytes()).hexdigest(),
        'header_graphs_complete':26425,'exact_episode_routes':selected['exact_episode_routes'],
        'explicit_compaction_header_bindings':audited,'unexplained_fallbacks_used':0,
        'saved_bounds_feet':result['bounds'],'finite_outline_boxes':result['accepted_bounds'],
        'invalid_outline_boxes':result['excluded_empty_or_unbounded_boxes'],
        'outside_variant_translation_xy_feet':[400,0],
        'outside_wall_min_x_feet':519.5,'x_clearance_from_saved_bounds_feet':519.5-result['bounds'][1][0],
        'scope':'All independently selected current saved header Outline boxes; not proof of evaluated/regenerated geometry bounds.'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reader-source',type=Path,required=True)
    p.add_argument('--target',type=Path,required=True);p.add_argument('source',type=Path)
    p.add_argument('--selection',type=Path,default=Path(__file__).parent/'results/record-selection.json')
    p.add_argument('--result',type=Path,required=True);a=p.parse_args()
    result=run(a.reader_source,a.source,a.target,a.selection)
    a.result.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('header_graphs_complete','finite_outline_boxes','unexplained_fallbacks_used','x_clearance_from_saved_bounds_feet')}))
