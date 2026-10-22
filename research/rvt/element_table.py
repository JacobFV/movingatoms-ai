"""Strict, byte-preserving project ElemTable codec for tested 28/40-byte profiles.

Only ID/owner framing and the schema-identified IdentifierSource.m_last are
interpreted. Other record fields and trailer bytes remain opaque. Updating
this table alone does not create a valid Revit element or save transaction.
"""
from dataclasses import dataclass
import struct

@dataclass(frozen=True)
class Table:
    tag: int
    width: int
    rows: tuple[bytes,...]
    trailer: bytes

    @property
    def stride(self):return 28 if self.width==4 else 40
    @property
    def last_id(self):
        at=11 if self.width==4 else 12
        return int.from_bytes(self.trailer[at:at+self.width],'little')
    def current(self,row):
        at=4 if self.width==4 else 20
        return int.from_bytes(row[at:at+self.width],'little')
    def primary(self,row):return int.from_bytes(row[:self.width],'little')
    def owner(self,row):
        at=24 if self.width==4 else 28
        value=int.from_bytes(row[at:at+self.width],'little')
        return None if value==(1<<(8*self.width))-1 else value
    def episode(self,row):return struct.unpack_from('<I',row,8)[0]


def validate(table):
    if table.width not in (4,8):raise ValueError('unsupported element ID width')
    tail=table.trailer
    expected=19 if table.width==4 else 24
    if len(tail)!=expected or tail[:8]!=b'\x00'*4+b'\xff'*4:
        raise ValueError('unsupported project table trailer')
    # Keep the class tag and all other bytes. These are profile constraints,
    # not a claim that the reserved bytes may be altered safely.
    at=11 if table.width==4 else 12
    if any(tail[10:at]) or any(tail[at+table.width:]):
        raise ValueError('unsupported identifier-source framing')
    if any(len(row)!=table.stride for row in table.rows):raise ValueError('wrong table record width')
    ids=[table.current(row)for row in table.rows]
    if any(a>=b for a,b in zip(ids,ids[1:])):raise ValueError('IDs must increase strictly')
    sentinel=(1<<(8*table.width))-1
    if ids and (ids[-1]>=sentinel or table.last_id<ids[-1]):raise ValueError('invalid ID ceiling/sentinel')
    owners={table.current(row):table.owner(row)for row in table.rows}
    if any(owner is not None and owner not in owners for owner in owners.values()):
        raise ValueError('owner is not a declared ID')
    done=set();depths={}
    for ident in ids:
        current=ident;chain=[];seen=set()
        while current is not None and current not in done:
            if current in seen:raise ValueError('owner cycle')
            seen.add(current);chain.append(current);current=owners[current]
        depth=depths.get(current,0)
        for node in reversed(chain):depth+=1;depths[node]=depth
        done.update(chain)
    return {'records':len(ids),'owner_links':sum(o is not None for o in owners.values()),
            'maximum_owner_chain_nodes':max(depths.values(),default=0),
            'primary_current_id_differences':sum(table.primary(r)!=table.current(r)for r in table.rows),
            'last_id':table.last_id,'maximum_current_id':max(ids,default=None)}


def decode(data,width):
    if width not in (4,8) or len(data)<6:raise ValueError('unsupported/truncated element table')
    tag,count=struct.unpack_from('<HI',data)
    stride=28 if width==4 else 40
    end=6+count*stride
    if end>len(data):raise ValueError('truncated element records')
    table=Table(tag,width,tuple(data[i:i+stride]for i in range(6,end,stride)),data[end:])
    validate(table)
    return table


def encode(table):
    validate(table)
    return struct.pack('<HI',table.tag,len(table.rows))+b''.join(table.rows)+table.trailer
