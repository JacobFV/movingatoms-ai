"""Lossless observed BasicFileInfo identity framing, with opaque bytes retained.

Supports the six audited streams whose first uint32 is 14. This is a guarded structural
patcher, not a semantic decoder for every binary metadata field.
"""
from dataclasses import dataclass
import struct
import uuid

COUNTERS = ('Unique Document Increments',
            "Central model's version number corresponding to the last reload latest")
GUIDS = ('Unique Document GUID',
         "Central model's episode GUID corresponding to the last reload latest")


def occurrences(data, needle):
    return [i for i in range(len(data)) if data.startswith(needle, i)]


def wide(value):
    raw = value.encode('utf-16-le')
    return struct.pack('<I', len(raw)//2)+raw


@dataclass(frozen=True)
class Identity:
    source: bytes
    text_start: int
    guid: str
    increments: int
    binary_counter: int
    binary_guid_spans: tuple
    binary_counter_string: tuple
    text_spans: dict


def decode(data):
    if len(data) < 4 or struct.unpack_from('<I', data)[0] != 14:
        raise ValueError('unsupported BasicFileInfo header')
    starts = occurrences(data, 'Worksharing:'.encode('utf-16-le'))
    if len(starts) != 1 or starts[0] < 2 or data[starts[0]-2:starts[0]] != b'\r\n':
        raise ValueError('unsupported BasicFileInfo text boundary')
    text_start = starts[0]
    spans = {}
    values = {}
    for key in COUNTERS+GUIDS:
        prefix = (key+': ').encode('utf-16-le')
        positions = occurrences(data[text_start:], prefix)
        if len(positions) != 1:
            raise ValueError('missing/ambiguous identity property')
        start = text_start+positions[0]+len(prefix)
        end = data.find(b'\r\0\n\0', start)
        if end < start or (end-start)%2:
            raise ValueError('invalid property terminator')
        try:
            values[key] = data[start:end].decode('utf-16-le')
        except UnicodeDecodeError as error:
            raise ValueError('invalid property text') from error
        spans[key] = (start, end)
    if values[COUNTERS[0]] != values[COUNTERS[1]] or values[GUIDS[0]] != values[GUIDS[1]]:
        raise ValueError('text identity copies disagree')
    number = values[COUNTERS[0]]
    if not number.isascii() or not number.isdigit() or str(int(number)) != number:
        raise ValueError('unsupported decimal counter')
    increments = int(number)
    if increments > 0x7fffffff:
        raise ValueError('counter outside observed signed range')
    guid = values[GUIDS[0]]
    try:
        if str(uuid.UUID(guid)) != guid:
            raise ValueError('noncanonical GUID')
    except (ValueError, AttributeError) as error:
        raise ValueError('invalid document GUID') from error
    guid_record = wide(guid)
    positions = occurrences(data[:text_start], guid_record)
    if len(positions) != 2 or positions[1] != positions[0]+len(guid_record):
        raise ValueError('unsupported binary GUID pair framing')
    counter = positions[0]-4
    if counter < 4 or struct.unpack_from('<I', data, counter)[0] != increments:
        raise ValueError('binary counter disagrees')
    counter_string_start = positions[1]+len(guid_record)
    counter_record = wide(number)
    if data[counter_string_start:counter_string_start+len(counter_record)] != counter_record:
        raise ValueError('binary decimal counter disagrees')
    end = counter_string_start+len(counter_record)
    # The next observed record is a 36-code-unit model identity GUID. Validate
    # its framing to establish that the decimal string is an independent record.
    if end+76 > text_start or struct.unpack_from('<I', data, end)[0] != 36:
        raise ValueError('unsupported following model identity record')
    try:
        uuid.UUID(data[end+4:end+76].decode('utf-16-le'))
    except (ValueError, UnicodeDecodeError) as error:
        raise ValueError('invalid following model identity') from error
    return Identity(data, text_start, guid, increments, counter,
                    tuple((p, p+len(guid_record)) for p in positions),
                    (counter_string_start, end), spans)


def encode(identity, increments=None, document_guid=None):
    # Revalidate the entire supplied source rather than trusting mutable spans.
    if decode(identity.source) != identity:
        raise ValueError('identity evidence changed')
    increments = identity.increments if increments is None else increments
    if type(increments) is not int or not 0 <= increments <= 0x7fffffff:
        raise ValueError('invalid document increment')
    try:
        guid = identity.guid if document_guid is None else str(uuid.UUID(document_guid))
    except (ValueError, AttributeError, TypeError) as error:
        raise ValueError('invalid document GUID') from error
    patches = [(identity.binary_counter, identity.binary_counter+4, struct.pack('<I', increments)),
               (*identity.binary_counter_string, wide(str(increments)))]
    patches.extend((start, end, wide(guid)) for start, end in identity.binary_guid_spans)
    patches.extend((*identity.text_spans[key], str(increments).encode('utf-16-le')) for key in COUNTERS)
    patches.extend((*identity.text_spans[key], guid.encode('utf-16-le')) for key in GUIDS)
    patches.sort()
    if any(a[1] > b[0] for a, b in zip(patches, patches[1:])):
        raise ValueError('overlapping identity spans')
    result = bytearray(identity.source)
    for start, end, replacement in reversed(patches):
        result[start:end] = replacement
    output = bytes(result)
    verified = decode(output)
    if verified.increments != increments or verified.guid != guid:
        raise ValueError('encoded identity mismatch')
    return output
