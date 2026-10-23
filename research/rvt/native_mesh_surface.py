"""Triangle surfaces with explicit topology reports and signed16 primitive chunks.

Open/disconnected/nonmanifold surfaces are not declared solids. Face winding is
preserved. Only exactly coincident input vertices are welded.
"""
from collections import defaultdict
import hashlib
import math
import struct
from native_mesh import measured_encoder,float32,sub,cross,norm


def encode_surface(profile,points,triangles,*,chunk_vertex_limit=32768):
    if type(chunk_vertex_limit)is not int or not 3<=chunk_vertex_limit<=32768:
        raise ValueError('chunk vertex limit must be3..32768')
    if not isinstance(points,(list,tuple))or not isinstance(triangles,(list,tuple))or not points or not triangles:
        raise ValueError('nonempty explicit point and triangle arrays required')
    encoder,_,_=measured_encoder(profile)
    welded=[];lookup={};input_to_welded=[]
    for point in points:
        if not isinstance(point,(list,tuple))or len(point)!=3 or any(type(v)not in(int,float)or not math.isfinite(v)for v in point):
            raise ValueError('finite XYZ coordinates required')
        key=tuple(point)
        if key not in lookup:lookup[key]=len(welded);welded.append(list(point))
        input_to_welded.append(lookup[key])
    quantized=[[float32(v)for v in p]for p in welded]
    if len({tuple(p)for p in quantized})!=len(quantized):raise ValueError('distinct input vertices collapse under float32')
    facets=[];normals=[];seen=set();used=set();edge_faces=defaultdict(list);vertex_faces=defaultdict(list)
    before_area=after_area=0.;maximum_normal_angle=0.
    for face_index,triangle in enumerate(triangles):
        if not isinstance(triangle,(list,tuple))or len(triangle)!=3 or any(type(i)is not int or not 0<=i<len(points)for i in triangle):
            raise ValueError('triangle input indices out of bounds')
        face=[input_to_welded[i]for i in triangle]
        if len(set(face))!=3:raise ValueError('degenerate welded face')
        key=tuple(sorted(face))
        if key in seen:raise ValueError('duplicate geometric face')
        seen.add(key);used.update(face);facets.append(face)
        for values in (welded,quantized):
            a,b,c=[values[i]for i in face];normal=cross(sub(b,a),sub(c,a));length=norm(normal)
            if not math.isfinite(length)or length<=0:raise ValueError('degenerate/nonfinite triangle before or after float32')
            if values is welded:
                before_area+=length/2;original_unit=[v/length for v in normal]
            else:
                after_area+=length/2;unit=[v/length for v in normal]
                cosine=sum(a*b for a,b in zip(original_unit,unit))
                if cosine<=0:raise ValueError('float32 changes triangle orientation by90degrees or more')
                maximum_normal_angle=max(maximum_normal_angle,math.acos(max(-1.,min(1.,cosine))))
                normals.append([float32(v)for v in unit])
        for u,v in zip(face,face[1:]+face[:1]):edge_faces[tuple(sorted((u,v)))].append((face_index,u,v))
        for v in face:vertex_faces[v].append(face_index)
    if used!=set(range(len(welded))):raise ValueError('isolated unused vertices are not triangle surfaces')
    adjacency={i:set()for i in range(len(facets))}
    for incident in edge_faces.values():
        ids=[entry[0]for entry in incident]
        for ident in ids[1:]:adjacency[ids[0]].add(ident);adjacency[ident].add(ids[0])
    remaining=set(adjacency);connected=[]
    while remaining:
        pending=[min(remaining)];component=set()
        while pending:
            face=pending.pop()
            if face in component:continue
            component.add(face);pending.extend(adjacency[face]-component)
        remaining-=component
        face_ids=sorted(component);vertices=set(v for f in face_ids for v in facets[f]);edges={tuple(sorted((u,v)))for f in face_ids for u,v in zip(facets[f],facets[f][1:]+facets[f][:1])}
        connected.append({'face_indices':face_ids,'vertices':len(vertices),'edges':len(edges),'faces':len(face_ids),
            'boundary_edges':sum(len(edge_faces[e])==1 for e in edges),'nonmanifold_edges':sum(len(edge_faces[e])>2 for e in edges),
            'euler_characteristic':len(vertices)-len(edges)+len(face_ids)})
    chunks=[];local_lookup={};global_vertices=[];local_faces=[];face_ids=[]
    def flush():
        if not local_faces:return
        fields={'m_normalsFlag':0,'m_commonNormal':[0.,0.,0.],
            'm_normalsArr':[normals[i]for i in face_ids],'m_pointsArr':[quantized[i]for i in global_vertices],
            'm_facetsArr':[t[:]for t in local_faces]}
        body=struct.pack('<H',1732)+encoder.fields(1732,fields)
        chunks.append({'body':body,'fields':fields,'audit':{'chunk_index':len(chunks),'global_vertex_indices':global_vertices[:],
            'input_face_indices':face_ids[:],'vertices':len(global_vertices),'triangles':len(local_faces),
            'body_sha256':hashlib.sha256(body).hexdigest(),'body_bytes':len(body)}})
    for i,face in enumerate(facets):
        added={v for v in face if v not in local_lookup}
        if len(local_lookup)+len(added)>chunk_vertex_limit:
            flush();local_lookup={};global_vertices=[];local_faces=[];face_ids=[]
        for vertex in face:
            if vertex not in local_lookup:local_lookup[vertex]=len(global_vertices);global_vertices.append(vertex)
        local_faces.append([local_lookup[v]for v in face]);face_ids.append(i)
    flush()
    emitted=[i for chunk in chunks for i in chunk['audit']['input_face_indices']]
    if emitted!=list(range(len(triangles))):raise ValueError('chunking changed face order or inventory')
    errors=[[abs(a-b)for a,b in zip(p,q)]for p,q in zip(welded,quantized)]
    winding_conflicts=[edge for edge,inc in edge_faces.items()if len(inc)==2 and inc[0][1:]!=inc[1][1:][::-1]]
    report={'source_sha256':profile['source_sha256'],'input_vertices':len(points),'welded_vertices':len(welded),
        'exact_welded_duplicates':len(points)-len(welded),'input_to_welded_vertex':input_to_welded,
        'input_triangles':len(triangles),'emitted_triangles':len(emitted),'face_order_and_winding_preserved':True,
        'chunk_count':len(chunks),'chunk_vertex_limit':chunk_vertex_limit,'connected_components':connected,
        'edge_connected_component_count':len(connected),'boundary_edge_count':sum(len(v)==1 for v in edge_faces.values()),
        'nonmanifold_edge_count':sum(len(v)>2 for v in edge_faces.values()),'paired_edge_winding_conflict_count':len(winding_conflicts),
        'winding_conflict_edges':[list(e)for e in winding_conflicts],
        'maximum_coordinate_error':max(v for row in errors for v in row),
        'maximum_vertex_displacement':max(math.dist(p,q)for p,q in zip(welded,quantized)),
        'maximum_face_normal_angle_error_radians':maximum_normal_angle,
        'surface_area_before_quantization':before_area,'surface_area_after_quantization':after_area,
        'solid_volume_claim':False,'self_intersections_checked':False,'autodesk_acceptance':'not_tested',
        'units':'feet','normal_binding':'one float32 unit normal per triangle; pinned public saved-graphics contract'}
    return {'components':chunks,'report':report}


def open_plane():return [[0.,0.,0.],[1.,0.,0.],[1.,1.,0.],[0.,1.,0.]],[[0,1,2],[0,2,3]]


def two_components():
    p,t=open_plane();return p+[[x+3,y,z]for x,y,z in p],t+[[i+4 for i in tri]for tri in t]


def large_index_surface(count=11000):
    points=[];triangles=[]
    for i in range(count):
        base=len(points);x=i*3.;points.extend([[x,0.,0.],[x+1,0.,0.],[x,1.,0.]]);triangles.append([base,base+1,base+2])
    return points,triangles
