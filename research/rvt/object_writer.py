"""Experimental object repacking; does not regenerate SignatureMarker fields.

Uses the recovered whole/start/middle/end framing. Compression boundaries are
chosen deterministically, not claimed identical to Autodesk's writer.
"""
from dataclasses import replace
import gzip
from partition_segments import Member, MAX_INFLATED_MEMBER
from partition_objects import encode_record, validate


def pack_records(items, sequence, width, limit=128*1024):
    header = width + 4 + (4 if sequence != 101 else 0)
    if width not in (4,8) or sequence not in (101,102,103):
        raise ValueError('unsupported object profile')
    if not header+4 <= limit <= MAX_INFLATED_MEMBER:
        raise ValueError('unsupported member size limit')
    members = []
    whole = bytearray()
    count = body_length = 0

    def emit(kind, n, length, payload):
        members.append(Member(kind,n,length,sequence,gzip.compress(payload,mtime=0)))

    def flush():
        nonlocal whole, count, body_length
        if count:
            emit(4,count,body_length,whole)
            whole=bytearray();count=body_length=0

    for record in items:
        wire = encode_record(record,sequence,width)
        if len(wire) <= limit:
            if len(whole)+len(wire)>limit:flush()
            whole.extend(wire);count+=1;body_length+=len(record.body)
            continue
        flush()
        first = min(limit-header,len(record.body)-1)
        emit(6,1,first,wire[:header+first])
        pos = first
        while len(record.body)-pos+4 > limit:
            length = min(limit,len(record.body)-pos-1)
            emit(7,0,length,record.body[pos:pos+length]);pos+=length
        emit(5,0,len(record.body)-pos,record.body[pos:]+wire[-4:])
    flush()
    return tuple(members)


def replace_records(segment, width, edits, limit=128*1024):
    """Replace bodies with explicit old-record preconditions; IDs cannot change.

edits maps (sequence, ID) to (expected Record, replacement Record).
Unchanged sequences keep their original compressed bytes and all footer bytes
are preserved. A changed footer's authenticity remains unverified.
    """
    original = validate(segment,width)
    changed = {seq:list(items) for seq,items in original.items()}
    if not edits:raise ValueError('no record edits')
    sentinel=(1<<(width*8))-1
    for (seq,ident),(expected,new) in edits.items():
        if seq not in changed or ident==sentinel or expected.element_id!=ident or new.element_id!=ident:
            raise ValueError('invalid edit key or changed ID')
        positions=[i for i,r in enumerate(changed[seq]) if r.element_id==ident]
        if len(positions)!=1 or changed[seq][positions[0]]!=expected:
            raise ValueError('record precondition failed')
        if new==expected:raise ValueError('record edit made no change')
        changed[seq][positions[0]]=new
    members=[]
    for seq,items in changed.items():
        if items==original[seq]:members.extend(m for m in segment.members if m.sequence==seq)
        else:members.extend(pack_records(items,seq,width,limit))
    result=replace(segment,members=tuple(members))
    if validate(result,width)!=changed:raise ValueError('repacked records differ from requested edit')
    return result
