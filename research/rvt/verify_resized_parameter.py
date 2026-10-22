"""Check the resized edit against independent reader and IFC projections."""
import argparse
import hashlib
import json
from pathlib import Path
from validation_bundle import canonical_ifc


def verify(root,value):
    expected=json.loads((root/'architecture-elements.json').read_bytes())
    actual=json.loads((root/'resized-elements.json').read_bytes())
    fields=[f for e in expected if e['id']==348738 and e['class_name']=='Room'
            for f in e['fields'] if f['name']=='m_room_floor_finish']
    if len(fields)!=1 or fields[0]['value']!='Wood':raise ValueError('unexpected source property')
    fields[0]['value']=value
    if expected!=actual:raise ValueError('unexpected reader-visible changes')
    before=canonical_ifc((root/'architecture-original.ifc').read_bytes()).splitlines()
    after=canonical_ifc((root/'resized-finish.ifc').read_bytes()).splitlines()
    if len(before)!=len(after):raise ValueError('IFC line count changed')
    changes=[(a,b) for a,b in zip(before,after) if a!=b]
    if len(changes)!=1:raise ValueError('expected exactly one IFC property change')
    a,b=changes[0]
    # This verifier deliberately accepts only plain ASCII without IFC quoting.
    if not value.isascii() or any(c in value for c in "'\\\r\n"):
        raise ValueError('unsupported IFC string comparison profile')
    needle=b"IFCPROPERTYSINGLEVALUE('FloorCovering',$,IFCLABEL('Wood'),$)"
    if needle not in a or b!=a.replace(b"IFCLABEL('Wood')",b"IFCLABEL('"+value.encode()+b"')"):
        raise ValueError('unexpected IFC property change')
    return {'reader_commit':'b6086d41b9758fd9b92f42f0a47b8345b9c58056',
            'element_count':len(actual),'changed_element':348738,
            'changed_field':'m_room_floor_finish','old':'Wood','new':value,
            'all_other_element_fields_identical':True,
            'ifc_changes_excluding_export_timestamps':1,
            'ifc_before_line':a.decode(),'ifc_after_line':b.decode(),
            'output_sha256':hashlib.sha256((root/'resized-finish.rvt').read_bytes()).hexdigest(),
            'autodesk_acceptance':'not_tested'}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path)
    p.add_argument('--value',default='Polished concrete');a=p.parse_args()
    print(json.dumps(verify(a.root,a.value),indent=2))
