"""Guarded twelve-foot wall variant, reusing the verified outside-save metadata."""
import argparse
import hashlib
import json
from pathlib import Path
import wall_candidate
from partition_builder import build_partition
from partition_objects import Record
from partition_segments import encode


def make(source,destination,profile,identity_evidence,registration_evidence,*,acknowledge_hypotheses=False):
    if not acknowledge_hypotheses:raise ValueError('explicit parametric/save/nonbounding hypotheses acknowledgment required')
    from wall_parametric import encode_wall
    # Construct all coordinated metadata through the existing guarded path.
    # Only the fresh, unpublished partition payload is then replaced.
    plan=wall_candidate.make(source,destination,profile,identity_evidence,
        acknowledge_hypotheses=True,registration_evidence=registration_evidence,
        synchronize_ancillary=True,translation_xy=(400.0,0.0),room_bounding=False)
    result=encode_wall(profile,133210,length_feet=12.0,translation_xy=(400.0,0.0),
        context=profile['external_references'],room_bounding=False,acknowledge_bounding_hypothesis=True)
    bodies,graphs,audit=result
    plan['geometry_moves']=audit['translation_moves']
    plan['parametric_encoder_audit']={k:v for k,v in audit.items()if k!='translation_moves'}
    if set(bodies)!={101,102,103}:raise ValueError('requires all three parametric channels')
    partition=build_partition(0x37b,{ch:(Record(133210,body),)for ch,body in bodies.items()},8,allow_unsigned_nonempty=True)
    payload=encode(partition);(destination/'partition.bin').write_bytes(payload)
    plan.update({'parametric_length_feet':12.0,'source_length_feet':9.5,
                 'channel_body_bytes':{str(ch):len(body)for ch,body in bodies.items()},
                 'parametric_body_sha256':{str(ch):hashlib.sha256(body).hexdigest()for ch,body in bodies.items()},
                 'partition_payload_sha256':hashlib.sha256(payload).hexdigest(),
                 'expected_bbox_feet':{'minimum':[519.5,67.41666666666663,76.0],'maximum':[531.5,68.08333333333333,91.0]},
                 'parametric_lifecycle_unproven':True})
    return plan

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('destination',type=Path)
    p.add_argument('--acknowledge-hypotheses',action='store_true');a=p.parse_args();results=Path(__file__).parent/'results'
    print(json.dumps(make(a.source,a.destination,json.loads((results/'wall-element-profile.json').read_bytes()),
        json.loads((results/'save-identity.json').read_bytes()),json.loads((results/'wall-element-registration.json').read_bytes()),
        acknowledge_hypotheses=a.acknowledge_hypotheses),indent=2))
