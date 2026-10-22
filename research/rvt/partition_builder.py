"""Construct experimental partition envelopes from complete object records.

This is not a class-body encoder. Nonempty unsigned groups require an explicit
opt-in because no source fixture proves Autodesk accepts that representation.
"""
from partition_objects import Record, validate
from partition_segments import Partition, Segment, encode, decode, PROFILES
from object_writer import pack_records


def build_partition(root_tag, records_by_sequence, id_width, trailing_zero=False,
                    *, allow_unsigned_nonempty=False, member_limit=128*1024):
    if root_tag not in PROFILES or id_width != (4 if root_tag == 0x365 else 8):
        raise ValueError('partition tag and ID width disagree')
    if type(trailing_zero) is not bool or type(allow_unsigned_nonempty) is not bool:
        raise ValueError('partition switches must be booleans')
    if set(records_by_sequence) != {101,102,103}:
        raise ValueError('exactly three object sequences are required')
    groups={seq:list(records_by_sequence[seq]) for seq in (101,102,103)}
    ids=[r.element_id for r in groups[101]]
    sentinel=(1<<(8*id_width))-1
    if any(not 0<=ident<sentinel for ident in ids) or len(ids)!=len(set(ids)):
        raise ValueError('invalid or duplicate element IDs; sentinels are added by the builder')
    if len(ids)>0xffffffff:raise ValueError('too many partition records')
    if any([r.element_id for r in records]!=ids for records in groups.values()):
        raise ValueError('ordered element IDs differ between sequences')
    if ids and not allow_unsigned_nonempty:
        raise ValueError('unsigned nonempty partition requires explicit experimental opt-in')
    for records in groups.values():records.append(Record(sentinel,b''))
    members=tuple(m for seq,records in groups.items()
                  for m in pack_records(records,seq,id_width,member_limit))
    segment=Segment(len(ids),None,members,b'',b'')
    if validate(segment,id_width)!=groups:raise ValueError('constructed records differ')
    result=Partition(root_tag,(segment,),trailing_zero)
    if decode(encode(result))!=result:raise ValueError('constructed partition did not round trip')
    return result
