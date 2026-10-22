"""Audit byte-extracted source previews; no rendering or native-save claim."""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import zlib
import olefile
from PIL import Image
from codec import decode as unpage
from fetch_fixture import FILES,HOLDOUTS
from save_history import decode as history_decode,GUID_NAMES
from save_increments import decode as increments_decode

PNG=b'\x89PNG\r\n\x1a\n'
FIELDS=('m_compressedImage','m_dpiX','m_dpiY','m_widthInFeet','m_heightInFeet','m_width','m_height')


def sha(data):return hashlib.sha256(data).hexdigest()


def extract(data):
    starts=[i for i in range(len(data)) if data.startswith(PNG,i)]
    if len(starts)!=1 or starts[0]<4:raise ValueError('nonunique/missing PNG marker')
    start=starts[0];length=struct.unpack_from('<I',data,start-4)[0];end=start+length
    if end+40!=len(data):raise ValueError('unexpected preview image length or suffix')
    prefix=data[:start-4];suffix=data[end:]
    field_offsets=[]
    for name in FIELDS:
        raw=struct.pack('<I',len(name))+name.encode('ascii');pos=prefix.find(raw)
        if pos<0 or prefix.find(raw,pos+1)>=0:raise ValueError('missing/ambiguous embedded image field')
        descriptor=struct.unpack_from('<I',prefix,pos+len(raw))[0]
        expected_descriptor=0x5002 if name=='m_compressedImage' else 4 if name in ('m_width','m_height') else 7
        if descriptor!=expected_descriptor:raise ValueError('unsupported embedded field descriptor')
        field_offsets.append(pos+4)
    if field_offsets!=sorted(field_offsets):raise ValueError('unexpected embedded field ordering')
    image=data[start:end];pos=8;chunks=[]
    while pos<len(image):
        if len(image)-pos<12:raise ValueError('truncated PNG chunk')
        size=struct.unpack_from('>I',image,pos)[0];kind=image[pos+4:pos+8];stop=pos+12+size
        if stop>len(image):raise ValueError('PNG chunk exceeds image')
        payload=image[pos+8:pos+8+size]
        if zlib.crc32(kind+payload)!=struct.unpack_from('>I',image,pos+8+size)[0]:raise ValueError('PNG chunk CRC mismatch')
        if not chunks and (kind!=b'IHDR' or size!=13):raise ValueError('PNG must start with IHDR')
        chunks.append({'type':kind.decode('ascii'),'bytes':size,'data_sha256':sha(payload)})
        pos=stop
        if kind==b'IEND':
            if size or pos!=len(image):raise ValueError('invalid PNG ending')
            break
    if not chunks or chunks[-1]['type']!='IEND':raise ValueError('missing PNG end')
    dpi_x,dpi_y,width_feet,height_feet,width,height=struct.unpack('<ddddii',suffix)
    if not all(math.isfinite(v) for v in (dpi_x,dpi_y,width_feet,height_feet)):
        raise ValueError('nonfinite image metadata')
    with Image.open(io.BytesIO(image)) as decoded:
        decoded.load();rgba=decoded.convert('RGBA')
        if decoded.size!=(width,height):raise ValueError('wrapper and PNG dimensions disagree')
        pixel_hash=sha(rgba.tobytes());mode=decoded.mode
        png_metadata={k:v for k,v in decoded.info.items() if k in ('dpi','gamma','srgb')}
    return image,{'stored_bytes':len(data),'stream_sha256':sha(data),'image_offset':start,
        'image_length_word_offset':start-4,'image_bytes':length,'image_sha256':sha(image),
        'prefix_bytes':len(prefix),'prefix_sha256':sha(prefix),'suffix_offset':end,
        'suffix_bytes':40,'suffix_sha256':sha(suffix),
        'embedded_field_name_offsets':dict(zip(FIELDS,field_offsets)),
        'tail_fields':dict(zip(FIELDS[1:],(dpi_x,dpi_y,width_feet,height_feet,width,height))),
        'png_chunks':chunks,'png_crc_verified':True,'decoded_mode':mode,
        'png_metadata':png_metadata,'rgba_pixel_sha256':pixel_hash,'pixel_dimensions':[width,height]},prefix,suffix


def value_matches(prefix,suffix,history,increments):
    latest=increments[-1];values={}
    for name,guid in zip(GUID_NAMES,history.guids):
        if guid!=b'\0'*16:values['History.'+name+'.bytes_le']=guid
    for i,episode in enumerate(history.episodes):values[f'History.episode[{i}].bytes_le']=episode[:16]
    integers={'history_episode_count':len(history.episodes),'increment_count':len(increments),
              'latest_increment_timestamp_low':latest['m_atimeStamp']['m_lsb']}
    integers.update({k:v for k,v in latest.items() if k.endswith('StreamRevision') and v>0})
    values.update((name+'.u32le',struct.pack('<I',v)) for name,v in integers.items())
    return [{'wrapper_part':part,'field':name,'offset':i,'bytes':len(value)}
            for part,data in [('prefix',prefix),('suffix',suffix)]
            for name,value in values.items() for i in range(len(data)-len(value)+1) if data.startswith(value,i)]


def run(directory,manifest,extract_dir=None):
    fixtures={n:h for _,n,h in FILES};fixtures.update(HOLDOUTS)
    for item in manifest['snapshots']:fixtures[item['file']]=item['sha256']
    reports=[]
    if extract_dir:extract_dir.mkdir(parents=True,exist_ok=True)
    for name,expected in fixtures.items():
        path=directory/name
        if path.parent.resolve()!=directory.resolve() or sha(path.read_bytes())!=expected:raise ValueError('fixture mismatch')
        with olefile.OleFileIO(path) as f:
            image,report,prefix,suffix=extract(f.openstream('RevitPreview4.0').read())
            def body(stream):
                raw=unpage(f.openstream('Global/'+stream).read())[8:];d=zlib.decompressobj(31);out=d.decompress(raw)
                if not d.eof or d.unconsumed_tail:raise ValueError('invalid global gzip')
                return out
            history=history_decode(body('History'));increments=increments_decode(body('DocumentIncrementTable'))[1]['m_increments']
        report.update(file=name,source_sha256=expected,preview_stream_revision=increments[-1]['m_previewStreamRevision'],
                      known_value_byte_matches=value_matches(prefix,suffix,history,increments))
        if extract_dir:
            filename=Path(name).stem+'.png';target=extract_dir/filename
            if target.exists() and target.read_bytes()!=image:raise ValueError('refusing to overwrite different preview extraction')
            target.write_bytes(image);report['extracted_filename']=filename
        reports.append(report)
    indexed={r['file']:r for r in reports};pairs=[]
    for before,after in zip(manifest['snapshots'],manifest['snapshots'][1:]):
        a,b=indexed[before['file']],indexed[after['file']]
        pairs.append({'before':a['file'],'after':b['file'],
            'preview_revisions':[a['preview_stream_revision'],b['preview_stream_revision']],
            **{field+'_equal':a[field]==b[field] for field in
               ('stream_sha256','prefix_sha256','suffix_sha256','image_sha256','rgba_pixel_sha256','pixel_dimensions')}})
    return {'fixtures':reports,'pairs':pairs,'source_preview_pixels_only':True,
            'known_value_matches_establish_semantics':False,'autodesk_acceptance':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path);p.add_argument('provenance',type=Path)
    p.add_argument('--extract-dir',type=Path);a=p.parse_args()
    print(json.dumps(run(a.directory,json.loads(a.provenance.read_bytes()),a.extract_dir),indent=2))
