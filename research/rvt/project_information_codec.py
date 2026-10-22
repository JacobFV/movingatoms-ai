"""Guarded timestamp-only edits to observed single-entry ProjectInformation ZIPs."""
from datetime import datetime, timezone
import hashlib
import io
import re
import struct
import xml.etree.ElementTree as ET
import zipfile
import zlib

UPDATED = {'{http://www.w3.org/2005/Atom}updated', '{urn:schemas-autodesk-com:partatom}updated'}


def parse(data):
    # EOCD is found structurally; comments/prefixes cannot silently become data.
    end = data.rfind(b'PK\x05\x06')
    if end < 0 or end+22 > len(data):
        raise ValueError('missing ZIP closing record')
    disk, central_disk, disk_entries, entries, central_size, central_offset, comment_size = struct.unpack_from('<HHHHIIH', data, end+4)
    if (disk or central_disk or disk_entries != 1 or entries != 1
            or end+22+comment_size != len(data) or central_offset+central_size != end):
        raise ValueError('unsupported ZIP directory layout')
    if data[:4] != b'PK\x03\x04' or data[central_offset:central_offset+4] != b'PK\x01\x02':
        raise ValueError('unsupported ZIP record signatures')
    flags, method = struct.unpack_from('<HH', data, 6)
    central_flags, central_method = struct.unpack_from('<HH', data, central_offset+8)
    if flags != 2 or central_flags != flags or method != 8 or central_method != method:
        raise ValueError('unsupported ZIP compression flags')
    crc, compressed_size, size = struct.unpack_from('<III', data, 14)
    central_fields = struct.unpack_from('<III', data, central_offset+16)
    if central_fields != (crc, compressed_size, size):
        raise ValueError('ZIP lengths or CRC disagree')
    local_name, local_extra = struct.unpack_from('<HH', data, 26)
    central_name, central_extra, central_comment = struct.unpack_from('<HHH', data, central_offset+28)
    if central_size != 46+central_name+central_extra+central_comment or struct.unpack_from('<I', data, central_offset+42)[0] != 0:
        raise ValueError('unsupported ZIP central entry')
    start = 30+local_name+local_extra
    if start+compressed_size != central_offset:
        raise ValueError('unsupported ZIP data descriptor or padding')
    d = zlib.decompressobj(-15)
    raw = d.decompress(data[start:central_offset])
    if not d.eof or d.unused_data or d.unconsumed_tail or len(raw) != size or zlib.crc32(raw) != crc:
        raise ValueError('invalid ZIP compressed payload')
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        info = archive.infolist()[0]
        if archive.read(info) != raw:
            raise ValueError('independent ZIP decoder differs')
    root = ET.fromstring(raw)
    nodes = [node for node in root.iter() if node.tag in UPDATED]
    values = [node.text for node in nodes]
    if {node.tag for node in nodes} != UPDATED or len(values) != 2 or values[0] != values[1] or values[0] is None:
        raise ValueError('unsupported XML timestamp fields')
    stamp = values[0]
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z', stamp):
        raise ValueError('unsupported XML timestamp syntax')
    if raw.count(stamp.encode('ascii')) != 2:
        raise ValueError('ambiguous XML timestamp byte locations')
    return raw, stamp, start, central_offset, end


def patch_timestamp(source, expected_sha256, source_increment_timestamp, new_increment_timestamp):
    """Return (stored ZIP bytes, evidence), preserving the source-derived offset.

    Timestamp offset preservation is an explicit hypothesis for a new save;
    it is not a general timezone or daylight-saving algorithm.
    """
    if hashlib.sha256(source).hexdigest() != expected_sha256:
        raise ValueError('ProjectInformation source changed')
    if any(type(v) is not int or not 0 <= v <= 0xffffffff for v in (source_increment_timestamp, new_increment_timestamp)):
        raise ValueError('unsupported increment timestamp')
    raw, old_stamp, start, central_offset, end = parse(source)
    old_seconds = int(datetime.fromisoformat(old_stamp.replace('Z', '+00:00')).timestamp())
    offset = source_increment_timestamp-old_seconds
    # Only the offsets established by the original six-file corpus are enabled.
    if offset not in (14400, 36000):
        raise ValueError('unsupported source timestamp offset')
    new_stamp = datetime.fromtimestamp(new_increment_timestamp-offset, timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    updated = raw.replace(old_stamp.encode('ascii'), new_stamp.encode('ascii'))
    evidence = {'source_sha256': expected_sha256,
        'source_timestamp_offset_seconds': offset,
        'source_increment_timestamp': source_increment_timestamp,
        'new_increment_timestamp': new_increment_timestamp,
        'timestamp_offset_policy': 'preserve_observed_source_offset_hypothesis',
        'changed_xml_text_fields': 0 if updated == raw else 2,
        'all_other_xml_bytes_preserved': True}
    if updated == raw:
        return source, evidence
    compressor = zlib.compressobj(level=9, wbits=-15)
    compressed = compressor.compress(updated)+compressor.flush()
    crc = zlib.crc32(updated)
    local = bytearray(source[:start]); central = bytearray(source[central_offset:end]); closing = bytearray(source[end:])
    struct.pack_into('<III', local, 14, crc, len(compressed), len(updated))
    struct.pack_into('<III', central, 16, crc, len(compressed), len(updated))
    struct.pack_into('<I', closing, 16, len(local)+len(compressed))
    result = bytes(local)+compressed+bytes(central)+bytes(closing)
    check, stamp, _, _, _ = parse(result)
    if check != updated or stamp != new_stamp:
        raise ValueError('updated ZIP verification failed')
    evidence['output_sha256'] = hashlib.sha256(result).hexdigest()
    evidence['zip_metadata_preserved_except_crc_sizes_directory_offset'] = True
    return result, evidence
