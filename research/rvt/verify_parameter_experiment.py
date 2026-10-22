"""Require exactly the intended reader-visible room property change."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
from validation_bundle import canonical_ifc


def verify(root):
    original=(root/'architecture-elements.json').read_bytes()
    edited=(root/'room-finish-elements.json').read_bytes()
    expected=json.loads(original);actual=json.loads(edited)
    rooms=[e for e in expected if e['id']==348738 and e['class_name']=='Room']
    if len(rooms)!=1:raise ValueError('expected one target room')
    fields=[f for f in rooms[0]['fields'] if f['name']=='m_room_floor_finish']
    if len(fields)!=1 or fields[0]['value']!='Wood':raise ValueError('unexpected original room finish')
    fields[0]['value']='Cork'
    if expected!=actual:raise ValueError('element output differs beyond the target field')
    controls={}
    for mode in ['recompress-control','footer-control']:
        controls[mode]=(root/(mode+'-elements.json')).read_bytes()==original
        if not controls[mode]:raise ValueError(f'{mode} changed element projection')
    old=canonical_ifc((root/'architecture-original.ifc').read_bytes()).splitlines()
    new=canonical_ifc((root/'room-finish.ifc').read_bytes()).splitlines()
    if len(old)!=len(new):raise ValueError('IFC line count changed')
    changes=[(a,b)for a,b in zip(old,new)if a!=b]
    if len(changes)!=1:raise ValueError('expected exactly one IFC property change')
    a,b=changes[0]
    if b"IFCPROPERTYSINGLEVALUE('FloorCovering',$,IFCLABEL('Wood'),$)" not in a or a.replace(b"IFCLABEL('Wood')",b"IFCLABEL('Cork')")!=b:
        raise ValueError('unexpected IFC property change')
    return {'reader_commit':'b6086d41b9758fd9b92f42f0a47b8345b9c58056','element_count':len(actual),
            'changed_element':348738,'changed_field':'m_room_floor_finish','old':'Wood','new':'Cork',
            'all_other_element_data_identical':True,'controls_element_json_byte_identical':controls,
            'ifc_changes_excluding_export_timestamps':1,'ifc_before_line':a.decode(),'ifc_after_line':b.decode(),
            'all_other_ifc_data_identical_except_export_timestamps':True,
            'element_output_sha256':hashlib.sha256(edited).hexdigest(),'revit_openability':'not_tested',
            'unknown_footer_integrity_verified':False,'complete_save_transaction':False}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('directory',type=Path)
    print(json.dumps(verify(p.parse_args().directory),indent=2))
