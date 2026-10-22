"""Verified 2024+ data-object envelopes and bounded, same-length text edits.

Wire facts cross-checked with public rvt-rs partition_room_parameters.rs at
b6086d41b9758fd9b92f42f0a47b8345b9c58056. No proprietary code is used.
These helpers do not update partition footer integrity or Revit save state.
"""
from dataclasses import dataclass
import struct
import zlib

@dataclass(frozen=True)
class Object:
    start: int
    end: int
    element_id: int
    class_tag: int


def verify(data,start):
    if start<0 or start+20>len(data):return None
    element,zero,checksum,size,cls=struct.unpack_from('<IIIII',data,start)
    end=start+20+size
    if zero or size<4 or end>len(data):return None
    if struct.unpack_from('<I',data,end-4)[0]!=size:return None
    if zlib.adler32(data[start+16:end-4])!=checksum:return None
    return Object(start,end,element,cls)


def enclosing(data,start,end):
    for pos in range(start-20,max(-1,start-200000),-1):
        obj=verify(data,pos)
        if obj and obj.end-4>=end:return obj
    return None


def text_entries(data,parameter):
    tag=struct.pack('<q',parameter);pos=0
    while (at:=data.find(tag,pos))>=0:
        pos=at+1
        if at+12>len(data):continue
        count=struct.unpack_from('<I',data,at+8)[0]
        end=at+12+count*2
        if count>256 or end>len(data):continue
        try:value=data[at+12:end].decode('utf-16le')
        except UnicodeDecodeError:continue
        obj=enclosing(data,at,end)
        if obj:yield obj,at+12,end,value


def replace_text(data,element,parameter,expected,new):
    old_bytes=expected.encode('utf-16le');new_bytes=new.encode('utf-16le')
    if len(old_bytes)!=len(new_bytes):raise ValueError('only equal UTF-16 byte lengths are supported')
    if old_bytes==new_bytes:raise ValueError('replacement must change the value')
    hits=[hit for hit in text_entries(data,parameter) if hit[0].element_id==element]
    if len(hits)!=1:raise ValueError('expected exactly one verified target parameter')
    obj,start,end,value=hits[0]
    if value!=expected:raise ValueError('old parameter value precondition failed')
    out=bytearray(data);out[start:end]=new_bytes
    checksum=zlib.adler32(out[obj.start+16:obj.end-4])
    struct.pack_into('<I',out,obj.start+8,checksum)
    if verify(out,obj.start)!=obj:raise ValueError('changed data-object checksum did not verify')
    return bytes(out),{'element_id':element,'parameter_id':parameter,'old':expected,'new':new,
                       'object_start':obj.start,'object_end':obj.end,'class_tag':obj.class_tag,
                       'value_start':start,'value_end':end,'new_adler32':f'{checksum:08x}'}


def replace_record_text(record,parameter,expected,new):
    """Resize one verified UTF-16 parameter in a 2024+ sequence-102 record.

    Matching remains constrained to the existing bounded parameter probe;
    arbitrary class layouts and nested string-length dependencies are not
    inferred. The caller must validate class semantics independently.
    """
    from partition_objects import Record,encode_record
    raw=encode_record(record,102,8)
    hits=list(text_entries(raw,parameter))
    if len(hits)!=1:raise ValueError('expected exactly one verified target parameter')
    obj,start,end,value=hits[0]
    if obj.start!=0 or obj.end!=len(raw) or obj.element_id!=record.element_id:
        raise ValueError('parameter is not in the target object')
    if value!=expected:raise ValueError('old parameter value precondition failed')
    replacement=new.encode('utf-16le')
    if value==new:raise ValueError('replacement must change the value')
    if len(replacement)//2>256:raise ValueError('text exceeds tested parameter profile')
    body=bytearray(record.body)
    body[start-16:end-16]=replacement
    struct.pack_into('<I',body,start-16-4,len(replacement)//2)
    result=Record(record.element_id,bytes(body))
    encoded=encode_record(result,102,8)
    check=verify(encoded,0)
    if not check or check.end!=len(encoded):raise ValueError('resized object did not verify')
    found=list(text_entries(encoded,parameter))
    if len(found)!=1 or found[0][3]!=new:raise ValueError('resized parameter did not round trip')
    return result
