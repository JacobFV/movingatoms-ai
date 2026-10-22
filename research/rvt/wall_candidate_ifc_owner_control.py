"""Explicit IFC OwnerHistory correction control, retaining uncorrected exports."""
import argparse
import hashlib
import json
from pathlib import Path
import ifcopenshell
from wall_candidate_ifc import run


def semantic(model):
    def value(v):
        if isinstance(v,ifcopenshell.entity_instance):return {'ref':v.id()}if v.id()else {'typed':v.is_a(),'value':value(v[0])}
        if isinstance(v,tuple):return [value(x)for x in v]
        return v
    return {e.id():{'class':e.is_a(),'values':[value(v)for v in e]}for e in model}


def correct(path,destination):
    model=ifcopenshell.open(str(path));before=semantic(model);histories=model.by_type('IfcOwnerHistory')
    if len(histories)!=1:raise ValueError('requires exactly one measured owner history')
    h=histories[0]
    if h.ChangeAction!='ADDED' or h.LastModifiedDate is not None or type(h.CreationDate)is not int or h.CreationDate<=0:
        raise ValueError('OwnerHistory does not match measured invalid ADDED-without-date profile')
    change={'step_id':h.id(),'attribute':'LastModifiedDate','before':None,'after':h.CreationDate,'source_creation_date':h.CreationDate}
    h.LastModifiedDate=h.CreationDate
    after=semantic(model);expected=json.loads(json.dumps(before));expected={int(k):v for k,v in expected.items()}
    expected[h.id()]['values'][4]=h.CreationDate
    if after!=expected:raise ValueError('unexpected semantic correction')
    if destination.exists():
        if semantic(ifcopenshell.open(str(destination)))!=expected:raise ValueError('existing control differs')
    else:model.write(str(destination))
    if semantic(ifcopenshell.open(str(destination)))!=expected:raise ValueError('serialized correction changes other attributes')
    return {'input_file':path.name,'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
            'output_file':destination.name,'output_sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),
            'change':change,'all_other_entities_and_attributes_preserved':True,'entities_compared':len(before)}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('candidate',type=Path);p.add_argument('--new-guid',required=True)
    p.add_argument('--translation',type=float,nargs=2,default=(30.0,20.0));a=p.parse_args()
    outputs=[f.with_name(f.stem+'-owner-corrected.ifc')for f in(a.source,a.candidate)]
    changes=[correct(f,out)for f,out in zip((a.source,a.candidate),outputs)]
    result=run(*outputs,a.new_guid,a.translation)
    if any(r['validation_messages']for r in result['schema_validation']):raise ValueError('corrected IFC still has schema findings')
    result['explicit_owner_history_correction_controls']=changes
    result['correction_script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result['native_rvt_modified']=False
    print(json.dumps(result,indent=2))
