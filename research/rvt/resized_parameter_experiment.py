"""Pinned variable-length room parameter experiment, not a complete Revit save."""
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import olefile
from codec import decode as unpage
from partition_segments import decode,encode
from partition_objects import validate
from object_writer import replace_records
from data_objects import replace_record_text
from parameter_experiment import SOURCE_SHA,STREAM,ELEMENT,PARAMETER


def make(source,dest,value):
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:
        raise ValueError('requires pinned MIT Architecture fixture')
    with olefile.OleFileIO(source) as f:raw=f.openstream(STREAM).read()
    original=decode(unpage(raw));base=original.segments[0]
    records=validate(base,8)
    targets=[r for r in records[102] if r.element_id==ELEMENT]
    if len(targets)!=1:raise ValueError('expected one target record')
    old=targets[0];new=replace_record_text(old,PARAMETER,'Wood',value)
    edited=replace_records(base,8,{(102,ELEMENT):(old,new)})
    partition=replace(original,segments=(edited,)+original.segments[1:])
    payload=encode(partition)
    reread=validate(decode(payload).segments[0],8)
    changes=[(seq,a.element_id) for seq,items in records.items()
             for a,b in zip(items,reread[seq]) if a!=b]
    if changes!=[(102,ELEMENT)]:raise ValueError('unexpected record changes')
    dest.mkdir(parents=True,exist_ok=False)
    (dest/'partition.bin').write_bytes(payload)
    manifest={'input_sha256':SOURCE_SHA,'patches':[{'stream':STREAM,
        'expected_stored_sha256':hashlib.sha256(raw).hexdigest(),'new_payload_file':'partition.bin'}]}
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return {'source_sha256':SOURCE_SHA,'old':'Wood','new':value,'element':ELEMENT,
            'changed_records':changes,'body_bytes_before':len(old.body),'body_bytes_after':len(new.body),
            'members_before':len(base.members),'members_after':len(edited.members),
            'unchanged_sequences_byte_identical':all(
                [m for m in base.members if m.sequence==seq]==[m for m in edited.members if m.sequence==seq]
                for seq in (101,103)),
            'other_content_groups_byte_identical':original.segments[1:]==partition.segments[1:],
            'signature_preserved_but_not_regenerated':True,'save_bookkeeping_updated':False,
            'autodesk_acceptance':'not_tested','complete_native_export':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('source',type=Path);p.add_argument('dest',type=Path)
    p.add_argument('--value',default='Polished concrete')
    a=p.parse_args();print(json.dumps(make(a.source,a.dest,a.value),indent=2))
