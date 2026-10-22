"""Byte-exact DocumentIncrementTable codec for observed 2023–2025 profiles.

Field order is established from embedded schemas, independently decoded by the
pinned public reader. This codec does not decide which revisions a save changes.
"""
import struct

PROFILES = {1248, 1283, 1313}
REVISIONS = ('preview', 'global', 'history', 'elemTable', 'contentDocuments',
             'partitionTable', 'incrementTable', 'formats', 'basicFileInfo',
             'transmissionData', 'partAtom', 'projectXMLInfo')


class Cursor:
    def __init__(self, data): self.data, self.pos = data, 0
    def take(self, n):
        if n < 0 or n > len(self.data)-self.pos: raise ValueError('truncated increment table')
        out = self.data[self.pos:self.pos+n]; self.pos += n
        return out
    def number(self, fmt='i'): return struct.unpack('<'+fmt, self.take(struct.calcsize('<'+fmt)))[0]
    def count(self, minimum):
        n = self.number('I')
        if n > (len(self.data)-self.pos)//minimum: raise ValueError('impossible increment array count')
        return n
    def string(self):
        n = self.count(2)
        raw = self.take(2*n)
        return raw.decode('utf-16-le', errors='surrogatepass')


def decode(data):
    c = Cursor(data); tag = c.number('H')
    if tag not in PROFILES: raise ValueError('unsupported increment table profile')
    def entry():
        versions = [{'m_causedByIncrementNumber': c.number(), 'm_totalElements': c.number()}
                    for _ in range(c.count(8))]
        result = {'m_incrementVersions': versions, 'm_userName': c.string(), 'm_comment': c.string(),
                  'm_greatest': {'m_id': c.number()}, 'm_totalEpisodes': c.number(),
                  'm_atimeStamp': {'m_msb': c.number('I'), 'm_lsb': c.number('I')},
                  'm_majorVersion': c.number(), 'm_totalElements': c.number()}
        result.update((f'm_{name}StreamRevision', c.number()) for name in REVISIONS)
        flag = c.number('B')
        if flag not in (0, 1): raise ValueError('invalid overwrite flag')
        result['m_overwrite'] = bool(flag)
        return result
    fields = {name: [entry() for _ in range(c.count(85))]
              for name in ('m_increments', 'm_localIncrements')}
    if c.number('I') != 0:
        raise ValueError('nonempty increment permutation is unsupported')
    fields['m_permutation'] = []
    if c.take(4) != b'\0'*4 or c.pos != len(data): raise ValueError('unexpected table closing bytes')
    return tag, fields


def encode(tag, fields):
    if tag not in PROFILES: raise ValueError('unsupported increment table profile')
    if set(fields) != {'m_increments', 'm_localIncrements', 'm_permutation'}:
        raise ValueError('unexpected table fields')
    output = bytearray(struct.pack('<H', tag))
    def number(value, fmt='i'):
        try: output.extend(struct.pack('<'+fmt, value))
        except (struct.error, TypeError) as e: raise ValueError('invalid increment integer') from e
    def string(value):
        raw = value.encode('utf-16-le', errors='surrogatepass')
        number(len(raw)//2, 'I'); output.extend(raw)
    expected = {'m_incrementVersions', 'm_userName', 'm_comment', 'm_greatest', 'm_totalEpisodes',
                'm_atimeStamp', 'm_majorVersion', 'm_totalElements', 'm_overwrite'}
    expected.update(f'm_{name}StreamRevision' for name in REVISIONS)
    for name in ('m_increments', 'm_localIncrements'):
        number(len(fields[name]), 'I')
        for row in fields[name]:
            if set(row) != expected: raise ValueError('unexpected increment fields')
            number(len(row['m_incrementVersions']), 'I')
            for version in row['m_incrementVersions']:
                if set(version) != {'m_causedByIncrementNumber', 'm_totalElements'}:
                    raise ValueError('unexpected increment version fields')
                number(version['m_causedByIncrementNumber']); number(version['m_totalElements'])
            string(row['m_userName']); string(row['m_comment'])
            if set(row['m_greatest']) != {'m_id'} or set(row['m_atimeStamp']) != {'m_msb', 'm_lsb'}:
                raise ValueError('unexpected nested increment fields')
            number(row['m_greatest']['m_id']); number(row['m_totalEpisodes'])
            number(row['m_atimeStamp']['m_msb'], 'I'); number(row['m_atimeStamp']['m_lsb'], 'I')
            number(row['m_majorVersion']); number(row['m_totalElements'])
            for revision in REVISIONS: number(row[f'm_{revision}StreamRevision'])
            if type(row['m_overwrite']) is not bool: raise ValueError('invalid overwrite flag')
            number(int(row['m_overwrite']), 'B')
    if fields['m_permutation'] != []:
        raise ValueError('nonempty increment permutation is unsupported')
    number(0, 'I')
    output.extend(b'\0'*4)
    return bytes(output)
