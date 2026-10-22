import struct
import unittest
import zlib
from preview_audit import extract,PNG,FIELDS


def chunk(kind,data):
    return struct.pack('>I',len(data))+kind+data+struct.pack('>I',zlib.crc32(kind+data))


def fixture():
    prefix=b'opaque wrapper prefix'
    for name in FIELDS:
        descriptor=0x5002 if name=='m_compressedImage' else 4 if name in ('m_width','m_height') else 7
        prefix+=struct.pack('<I',len(name))+name.encode()+struct.pack('<I',descriptor)
    image=(PNG+chunk(b'IHDR',struct.pack('>IIBBBBB',1,1,8,6,0,0,0))+
           chunk(b'IDAT',zlib.compress(b'\0\xff\0\0\xff'))+chunk(b'IEND',b''))
    return prefix+struct.pack('<I',len(image))+image+struct.pack('<ddddii',72,72,0,0,1,1)


class PreviewAuditTests(unittest.TestCase):
    def test_exact_image_extraction_and_dimensions(self):
        data=fixture();image,report,prefix,suffix=extract(data)
        self.assertEqual(data,prefix+struct.pack('<I',len(image))+image+suffix)
        self.assertEqual(report['pixel_dimensions'],[1,1])
        self.assertTrue(report['png_crc_verified'])
        self.assertEqual([c['type'] for c in report['png_chunks']],['IHDR','IDAT','IEND'])

    def test_png_crc_length_and_dimensions_rejected(self):
        raw=fixture();start=raw.index(PNG)
        crc=bytearray(raw);crc[start+29]^=1
        length=bytearray(raw);length[start-4]^=1
        dimensions=bytearray(raw);dimensions[-8:]=struct.pack('<ii',2,1)
        descriptor=bytearray(raw);offset=raw.index(b'm_compressedImage')+len('m_compressedImage');descriptor[offset]^=1
        for data in (crc,length,dimensions,descriptor,raw[:-1],raw+b'\0'):
            with self.assertRaises(ValueError):extract(bytes(data))
