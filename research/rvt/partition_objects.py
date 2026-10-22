"""Strict object envelopes within length-framed partition segments.

Sequence 101 omits Adler-32; sequences 102/103 include it. Member kinds
4/6/7/5 encode whole/start/middle/end objects. Only byte framing is claimed.
"""
from dataclasses import dataclass
import struct
import zlib

@dataclass(frozen=True)
class Record:
    element_id: int
    body: bytes


def records(segment,id_width):
    if id_width not in (4,8):raise ValueError('unsupported ID width')
    groups={};pending=None;sequence=None
    for m in segment.members:
        if m.sequence not in (101,102,103):raise ValueError('unsupported object sequence')
        if m.sequence!=sequence:
            if pending:raise ValueError('unfinished object at sequence boundary')
            if m.sequence in groups:raise ValueError('noncontiguous sequence')
            groups[m.sequence]=[];sequence=m.sequence
        b=m.inflate();checksummed=sequence!=101
        header=id_width+4+4*checksummed
        def start(at):
            if at+header>len(b):raise ValueError('truncated object header')
            ident=int.from_bytes(b[at:at+id_width],'little')
            checksum=struct.unpack_from('<I',b,at+id_width)[0] if checksummed else None
            size=struct.unpack_from('<I',b,at+header-4)[0]
            return ident,checksum,size
        def finish(ident,checksum,body):
            if checksummed and zlib.adler32(body)!=checksum:raise ValueError('invalid object Adler-32')
            groups[sequence].append(Record(ident,body))
        if m.kind==4:
            if pending:raise ValueError('whole objects inside split object')
            pos=0;body_total=0
            for _ in range(m.count):
                ident,checksum,size=start(pos);pos+=header
                if pos+size+4>len(b):raise ValueError('truncated object body')
                body=b[pos:pos+size];pos+=size
                if struct.unpack_from('<I',b,pos)[0]!=size:raise ValueError('object length trailer mismatch')
                pos+=4;body_total+=size;finish(ident,checksum,body)
            if pos!=len(b) or body_total!=m.body_length:raise ValueError('whole-object member count/length mismatch')
        elif m.kind==6:
            if pending or m.count!=1:raise ValueError('invalid object start')
            ident,checksum,size=start(0);body=b[header:]
            if len(body)!=m.body_length or len(body)>=size:raise ValueError('invalid initial object fragment length')
            pending=(ident,checksum,size,bytearray(body))
        elif m.kind in (5,7):
            if not pending or m.count:raise ValueError('orphan object continuation')
            ident,checksum,size,body=pending
            if m.kind==7:
                if len(b)!=m.body_length:raise ValueError('middle fragment length mismatch')
                body.extend(b)
                if len(body)>=size:raise ValueError('middle fragment exhausts object')
            else:
                if len(b)!=m.body_length+4 or struct.unpack_from('<I',b,len(b)-4)[0]!=size:
                    raise ValueError('final fragment length trailer mismatch')
                body.extend(b[:-4])
                if len(body)!=size:raise ValueError('assembled object length mismatch')
                finish(ident,checksum,bytes(body));pending=None
        else:raise ValueError('unsupported object member kind')
    if pending:raise ValueError('unfinished final object')
    return groups


def encode_record(record,sequence,id_width):
    """Encode an object envelope, including Adler-32 and repeated body length."""
    if id_width not in (4,8) or sequence not in (101,102,103):
        raise ValueError('unsupported record profile')
    if not 0<=record.element_id<1<<(id_width*8) or len(record.body)>0xffffffff:
        raise ValueError('record ID/body length outside wire range')
    out=bytearray(record.element_id.to_bytes(id_width,'little'))
    if sequence!=101:out.extend(struct.pack('<I',zlib.adler32(record.body)))
    out.extend(struct.pack('<I',len(record.body)));out.extend(record.body)
    out.extend(struct.pack('<I',len(record.body)))
    return bytes(out)


def validate(segment,id_width):
    """Require the three matching ID lists, declared count and empty sentinel."""
    groups=records(segment,id_width)
    if list(groups)!=[101,102,103]:raise ValueError('expected ordered sequences 101/102/103')
    ids=[r.element_id for r in groups[101]]
    sentinel=(1<<(8*id_width))-1
    if len(ids)!=segment.count+1 or not ids or ids[-1]!=sentinel:
        raise ValueError('segment count/sentinel mismatch')
    if len(set(ids))!=len(ids):raise ValueError('duplicate object ID within sequence')
    for seq,items in groups.items():
        if [r.element_id for r in items]!=ids or items[-1].body:
            raise ValueError('sequence IDs/sentinel bodies disagree')
        wire=b''.join(encode_record(r,seq,id_width)for r in items)
        original=b''.join(m.inflate()for m in segment.members if m.sequence==seq)
        if wire!=original:raise ValueError('object encoder does not reproduce source bytes')
    return groups
