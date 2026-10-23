"""Closed convex FacetedTopology0 components; no element or document creation."""
from collections import Counter,defaultdict
import hashlib
import math
import struct
from wall_element import GraphEncoder
from directshape_mesh import encode_profile


def sub(a,b):return [x-y for x,y in zip(a,b)]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def norm(a):return math.sqrt(dot(a,a))
def float32(value):
    if type(value)not in(int,float)or not math.isfinite(value):raise ValueError('finite numeric float32 required')
    try: result=struct.unpack('<f',struct.pack('<f',value))[0]
    except (OverflowError,struct.error)as error:raise ValueError('float32 overflow')from error
    if not math.isfinite(result):raise ValueError('float32 overflow')
    return result


def measured_encoder(profile):
    bodies=encode_profile(profile)
    record=next(r for r in profile['records']if r['channel']==103)
    declarations=record['declarations'];classes={c['name']:c for c in declarations}
    facet=classes['FacetedTopology0'];field=facet['fields'][0]
    if len(facet['fields'])!=1 or field['name']!='m_facetsArr' or (field['base'],field['modifier'])!=(13,0x50):raise ValueError('unmeasured facet array descriptor')
    nested=field['nested_descriptor']
    if (nested['base'],nested['modifier'],nested['array_count'])!=(3,0x10,3):raise ValueError('requires measured signed16 index triples')
    if facet['tag']!=1732:raise ValueError('unsupported topology tag')
    return GraphEncoder(declarations),record,bodies[103]


def source_component(profile,index=0):
    encoder,record,body=measured_encoder(profile)
    components=[o for o in record['graph']['objects']if o['class_name']=='FacetedTopology0']
    if type(index)is not int or not 0<=index<len(components):raise ValueError('source component index')
    obj=components[index];fields=encoder.fields(obj['class_tag'],obj['fields'])
    if fields!=body[obj['start']:obj['fields_end']]:raise ValueError('source component field bytes differ')
    return struct.pack('<H',obj['class_tag'])+fields,obj['fields'],{'original_field_bytes_sha256':hashlib.sha256(fields).hexdigest(),'source_field_span':[obj['start'],obj['fields_end']],'original_103_sha256':record['source']['body_sha256'],'source_exact':True,'closed_solid_claim':False}


def audit_closed(points,triangles,*,allow_nonconvex=False):
    if type(allow_nonconvex)is not bool:raise ValueError('nonconvex policy must be boolean')
    if allow_nonconvex and len(triangles)>2048:raise ValueError('nonconvex intersection audit limited to2048 triangles')
    if not 4<=len(points)<=32768 or not 4<=len(triangles)<=65536:raise ValueError('bounded vertex/triangle inventory required')
    if any(len(p)!=3 or any(type(v)not in(int,float)or not math.isfinite(v)for v in p)for p in points):raise ValueError('finite XYZ triples required')
    if len({tuple(p)for p in points})!=len(points):raise ValueError('duplicate or quantization-collapsed vertices')
    edges=defaultdict(list);neighbors=defaultdict(set);vertex_links=defaultdict(list);used=set();seen=set();normals=[];areas=[]
    center=[sum(p[i]for p in points)/len(points)for i in range(3)]
    extent=max(max(p[i]for p in points)-min(p[i]for p in points)for i in range(3))
    if not math.isfinite(extent)or not extent>0:raise ValueError('zero extent')
    tolerance=max(1e-12,extent*1e-10);volume=0.;convex=True
    for ti,tri in enumerate(triangles):
        if len(tri)!=3 or any(type(i)is not int or not 0<=i<len(points)or i>32767 for i in tri)or len(set(tri))!=3:raise ValueError('invalid signed16 triangle indices')
        canonical=tuple(sorted(tri))
        if canonical in seen:raise ValueError('duplicate triangle')
        seen.add(canonical);used.update(tri)
        a,b,c=[points[i]for i in tri];normal=cross(sub(b,a),sub(c,a));size=norm(normal)
        if not math.isfinite(size)or size<=tolerance*tolerance:raise ValueError('degenerate triangle')
        unit=[v/size for v in normal]
        if dot(unit,sub(a,center))<=tolerance or any(dot(unit,sub(p,a))>tolerance for p in points):
            convex=False
            if not allow_nonconvex:raise ValueError('only closed convex nonintersecting components supported by default')
        normals.append(normal);areas.append(size/2)
        volume+=dot(sub(a,center),cross(sub(b,center),sub(c,center)))/6
        for u,v in ((tri[0],tri[1]),(tri[1],tri[2]),(tri[2],tri[0])):edges[tuple(sorted((u,v)))].append((u,v,ti))
        for i,v in enumerate(tri):vertex_links[v].append((tri[(i+1)%3],tri[(i+2)%3]))
    if used!=set(range(len(points))):raise ValueError('unused vertices')
    for incidences in edges.values():
        if len(incidences)!=2 or incidences[0][:2]!=incidences[1][:2][::-1]:raise ValueError('edge lacks opposite paired incidence')
        a,b=incidences[0][2],incidences[1][2];neighbors[a].add(b);neighbors[b].add(a)
    def connected(adjacency,start):
        reached=set();pending=[start]
        while pending:
            v=pending.pop()
            if v in reached:continue
            reached.add(v);pending.extend(adjacency[v]-reached)
        return reached
    if len(connected(neighbors,0))!=len(triangles):raise ValueError('disconnected components')
    for links in vertex_links.values():
        adjacency=defaultdict(set);degree=Counter()
        for a,b in links:adjacency[a].add(b);adjacency[b].add(a);degree[a]+=1;degree[b]+=1
        if any(v!=2 for v in degree.values())or len(connected(adjacency,next(iter(adjacency))))!=len(adjacency):raise ValueError('nonmanifold vertex link')
    euler=len(points)-len(edges)+len(triangles)
    if (not allow_nonconvex and euler!=2)or euler>2 or euler%2 or not math.isfinite(volume)or volume<=tolerance**3:raise ValueError('unsupported or inward closed solid topology')
    intersections=None
    if allow_nonconvex:
        from native_mesh_intersections import reject_intersections
        intersections=reject_intersections(points,triangles,tolerance)
    vertex_normals=[]
    for i in range(len(points)):
        v=[sum(normal[j]for tri,normal in zip(triangles,normals)if i in tri)for j in range(3)];size=norm(v)
        if size<=tolerance:raise ValueError('ambiguous vertex normal')
        vertex_normals.append([x/size for x in v])
    report={'vertices':len(points),'triangles':len(triangles),'edges':len(edges),'closed':True,'euler_characteristic':euler,
        'opposite_edge_incidence':True,'single_cycle_vertex_links':True,'convex':convex,'signed_volume':volume,'surface_area':sum(areas),
        'bounds':[[min(p[i]for p in points)for i in range(3)],[max(p[i]for p in points)for i in range(3)]],
        'vertex_normals':vertex_normals,'triangle_normals':[[v/norm(n)for v in n]for n in normals]}
    if allow_nonconvex:report.update(genus=(2-euler)//2,intersection_audit=intersections)
    return report


def encode_component(profile,points,triangles,*,allow_nonconvex=False):
    encoder,_,_=measured_encoder(profile)
    original=audit_closed(points,triangles,allow_nonconvex=allow_nonconvex)
    quantized=[[float32(v)for v in p]for p in points]
    measured=audit_closed(quantized,triangles,allow_nonconvex=allow_nonconvex)
    normals=[[float32(v)for v in n]for n in measured['triangle_normals']]
    fields={'m_normalsFlag':0,'m_commonNormal':[0.,0.,0.],'m_normalsArr':normals,'m_pointsArr':quantized,'m_facetsArr':[list(t)for t in triangles]}
    body=struct.pack('<H',1732)+encoder.fields(1732,fields)
    coordinate_errors=[[abs(a-b)for a,b in zip(p,q)]for p,q in zip(points,quantized)]
    report={'source_sha256':profile['source_sha256'],'topology_class':'FacetedTopology0','index_storage':'signed16 triples',
        'point_normal_storage':'float32 triples','normals_interpretation':'one outward unit normal per triangle; public saved-graphics cardinality contract, Autodesk shading untested',
        'original_geometry':original,'quantized_geometry':measured,'coordinate_absolute_errors':coordinate_errors,
        'maximum_coordinate_error':max(v for p in coordinate_errors for v in p),'maximum_vertex_displacement':max(math.dist(p,q)for p,q in zip(points,quantized)),
        'volume_error':abs(original['signed_volume']-measured['signed_volume']),
        'maximum_normal_unit_length_error':max(abs(norm(n)-1)for n in normals),
        'maximum_normal_component_rounding_error':max(abs(a-b)for p,q in zip(measured['triangle_normals'],normals)for a,b in zip(p,q)),
        'body_bytes':len(body),'body_sha256':hashlib.sha256(body).hexdigest(),'element_created':False,'autodesk_acceptance':'not_tested'}
    return body,fields,report


def cuboid(origin=(.1,.2,.3),size=(1.1,2.2,3.3)):
    points=[[origin[0]+x*size[0],origin[1]+y*size[1],origin[2]+z*size[2]]for x,y,z in ((0,0,0),(1,0,0),(1,1,0),(0,1,0),(0,0,1),(1,0,1),(1,1,1),(0,1,1))]
    triangles=[[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[1,2,6],[1,6,5],[2,3,7],[2,7,6],[3,0,4],[3,4,7]]
    return points,triangles


def tetrahedron():
    return [[.1,.2,.3],[1.2,.2,.3],[.1,2.4,.3],[.1,.2,3.6]],[[0,2,1],[0,1,3],[0,3,2],[1,2,3]]


def l_prism():
    polygon=[(0,0),(2,0),(2,1),(1,1),(1,2),(0,2)]
    points=[[x,y,z]for z in (0,1)for x,y in polygon]
    top=[[0,1,3],[1,2,3],[0,3,5],[3,4,5]]
    triangles=[t[::-1]for t in top]+[[i+6 for i in t]for t in top]
    for i in range(6):
        j=(i+1)%6;triangles.extend([[i,j,j+6],[i,j+6,i+6]])
    return points,triangles


def torus(major=2.,minor=.5,n=12,m=8):
    points=[];triangles=[]
    for i in range(n):
        u=2*math.pi*i/n
        for j in range(m):
            v=2*math.pi*j/m;points.append([(major+minor*math.cos(v))*math.cos(u),(major+minor*math.cos(v))*math.sin(u),minor*math.sin(v)])
    for i in range(n):
        for j in range(m):
            a=i*m+j;b=((i+1)%n)*m+j;c=((i+1)%n)*m+(j+1)%m;d=i*m+(j+1)%m
            triangles.extend([[a,b,c],[a,c,d]])
    return points,triangles
