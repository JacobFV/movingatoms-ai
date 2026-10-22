"""Pinned room-finish edit and matched controls; NOT Autodesk-validated writes.

Only known envelope/object checksums are updated. Unknown partition footer
integrity and save bookkeeping remain unresolved and are reported explicitly.
"""
import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import struct
import zlib
import olefile
from codec import decode as unpage
from partition_segments import decode,encode
from data_objects import replace_text
from partition_objects import validate

SOURCE_SHA='4a78bdd68e7f4dd7806060db07c222da9a810e20b3f303c17a443294b91c8ce4'
STREAM='Partitions/80'
ELEMENT=348738
PARAMETER=-1006903


def recompress(original,data):
    if original[:4]!=b'\x1f\x8b\x08\x00':raise ValueError('unsupported gzip header flags')
    c=zlib.compressobj(9,zlib.DEFLATED,-15)
    result=original[:10]+c.compress(data)+c.flush()+struct.pack('<II',zlib.crc32(data),len(data))
    if zlib.decompress(result,31)!=data:raise ValueError('recompressed member mismatch')
    return result


def replace_member_payloads(segment,old,new,force=()):
    if len(old)!=len(new):raise ValueError('member boundaries require equal-length payloads')
    members=[];offset=0;changed=[]
    for i,m in enumerate(segment.members):
        before=m.inflate();after=new[offset:offset+len(before)]
        if old[offset:offset+len(before)]!=before:raise ValueError('original segment precondition failed')
        if after!=before or i in force:
            m=replace(m,compressed=recompress(m.compressed,after));changed.append(i)
        members.append(m);offset+=len(before)
    if offset!=len(old):raise ValueError('segment payload length mismatch')
    return replace(segment,members=tuple(members)),changed


def make(source,dest,mode):
    if hashlib.sha256(source.read_bytes()).hexdigest()!=SOURCE_SHA:
        raise ValueError('experiment accepts only the pinned MIT RE1 Architecture fixture')
    with olefile.OleFileIO(source) as f:raw=f.openstream(STREAM).read()
    logical=unpage(raw);partition=decode(logical);base=partition.segments[0]
    original_records=validate(base,8)
    before=b''.join(m.inflate()for m in base.members)
    after,detail=replace_text(before,ELEMENT,PARAMETER,'Wood','Cork')
    edited,changed=replace_member_payloads(base,before,after)
    if mode=='recompress-control':
        edited,changed=replace_member_payloads(base,before,before,force=changed)
    elif mode=='footer-control':
        if len(base.footer)!=64:raise ValueError('expected nonempty footer')
        edited=replace(base,footer=bytes([base.footer[0]^1])+base.footer[1:]);changed=[]
    elif mode=='unsigned-control':
        edited=replace(base,footer=b'',label=b'');changed=[]
    elif mode=='unsigned-room-finish':
        edited=replace(edited,footer=b'',label=b'')
    elif mode!='room-finish':raise ValueError('unknown experiment')
    edited_records=validate(edited,8)
    record_changes=[(seq,a.element_id) for seq,items in original_records.items()
                    for a,b in zip(items,edited_records[seq]) if a!=b]
    expected_changes=[(102,ELEMENT)] if mode in ('room-finish','unsigned-room-finish') else []
    if record_changes!=expected_changes:raise ValueError('unexpected object record changes')
    new_partition=replace(partition,segments=(edited,)+partition.segments[1:])
    payload=encode(new_partition)
    if payload==logical:raise ValueError('experiment made no change')
    dest.mkdir(parents=True,exist_ok=False)
    (dest/'partition.bin').write_bytes(payload)
    manifest={'input_sha256':SOURCE_SHA,'patches':[{'stream':STREAM,
              'expected_stored_sha256':hashlib.sha256(raw).hexdigest(),'new_payload_file':'partition.bin'}]}
    (dest/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    return {'mode':mode,'source_sha256':SOURCE_SHA,'stream':STREAM,'changed_members':changed,
            'parameter_edit':detail if mode in ('room-finish','unsigned-room-finish') else None,
            'changed_object_records':record_changes,
            'all_object_counts_ids_lengths_and_adler32_verified':True,
            'all_unedited_segments_preserved':new_partition.segments[1:]==partition.segments[1:],
            'inflated_member_lengths_preserved':True,
            'footer_preserved':edited.footer==base.footer,
            'signature_fields_cleared':not edited.footer and not edited.label,
            'footer_integrity_regenerated':False,'save_bookkeeping_updated':False,
            'revit_openability':'not_tested','production_native_export':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('dest',type=Path)
    p.add_argument('--mode',required=True,choices=['room-finish','recompress-control','footer-control','unsigned-control','unsigned-room-finish'])
    a=p.parse_args();print(json.dumps(make(a.source,a.dest,a.mode),indent=2))
