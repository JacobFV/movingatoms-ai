"""Bounded triangle intersection checks, permitting only declared shared simplices."""
import itertools
import math


def sub(a,b):return [x-y for x,y in zip(a,b)]
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def norm(v):return math.sqrt(dot(v,v))


def inside(point,triangle,normal,tol):
    return all(dot(cross(sub(b,a),sub(point,a)),normal)>=-tol*max(norm(sub(b,a)),tol)
               for a,b in zip(triangle,triangle[1:]+triangle[:1]))


def coplanar_overlap(a,b,normal,tol):
    """Clip triangle A by the three in-plane halfspaces of triangle B."""
    output=[p[:]for p in a]
    for start,end in zip(b,b[1:]+b[:1]):
        edge=sub(end,start);length=norm(edge)
        def distance(p):return dot(cross(edge,sub(p,start)),normal)/length
        input_points=output;output=[]
        if not input_points:break
        previous=input_points[-1];before=distance(previous)
        for point in input_points:
            after=distance(point);pin=before>=-tol;cin=after>=-tol
            if pin!=cin:
                # Intersect the exact plane, not the tolerance-offset halfspace.
                denominator=before-after
                if abs(denominator)>tol*1e-3:
                    t=max(0.,min(1.,before/denominator))
                    output.append([previous[i]+t*(point[i]-previous[i])for i in range(3)])
            if cin:output.append(point)
            previous,before=point,after
    return output


def triangle_intersection(a,b,tol):
    if any(max(p[i]for p in a)<min(p[i]for p in b)-tol or max(p[i]for p in b)<min(p[i]for p in a)-tol for i in range(3)):return []
    normals=[]
    for tri in (a,b):
        n=cross(sub(tri[1],tri[0]),sub(tri[2],tri[0]));size=norm(n)
        if size<=tol*tol:raise ValueError('degenerate triangle intersection input')
        normals.append([x/size for x in n])
    distances=[[dot(n,sub(p,tri[0]))for p in other]for tri,other,n in ((a,b,normals[0]),(b,a,normals[1]))]
    if any(min(ds)>tol or max(ds)<-tol for ds in distances):return []
    if norm(cross(*normals))<1e-10:
        if max(abs(x)for ds in distances for x in ds)>tol:return []
        # B's normal controls clip orientation regardless of A's winding.
        return coplanar_overlap(a,b,normals[1],tol)
    points=[]
    for tri,other,n in ((a,b,normals[1]),(b,a,normals[0])):
        for start,end in zip(tri,tri[1:]+tri[:1]):
            ds=dot(n,sub(start,other[0]));de=dot(n,sub(end,other[0]))
            for p,d in ((start,ds),(end,de)):
                if abs(d)<=tol and inside(p,other,n,tol):points.append(p)
            if (ds>tol and de>tol)or(ds<-tol and de<-tol)or abs(ds-de)<=tol*1e-3:continue
            t=ds/(ds-de)
            if -1e-12<=t<=1+1e-12:
                p=[start[i]+t*(end[i]-start[i])for i in range(3)]
                if inside(p,other,n,tol):points.append(p)
    return points


def on_declared_simplex(point,shared,tol):
    if not shared:return False
    if len(shared)==1:return math.dist(point,shared[0])<=tol*4
    if len(shared)!=2:raise ValueError('duplicate triangle')
    a,b=shared;edge=sub(b,a);t=dot(sub(point,a),edge)/dot(edge,edge)
    closest=[a[i]+max(0.,min(1.,t))*edge[i]for i in range(3)]
    return math.dist(point,closest)<=tol*4


def reject_intersections(points,triangles,tolerance):
    if len(triangles)>2048:raise ValueError('nonconvex intersection audit limited to2048 triangles')
    checked=0;contacts=0
    for i,j in itertools.combinations(range(len(triangles)),2):
        first,second=triangles[i],triangles[j]
        intersection=triangle_intersection([points[v]for v in first],[points[v]for v in second],tolerance)
        checked+=1
        if not intersection:continue
        contacts+=1;shared=[points[v]for v in sorted(set(first)&set(second))]
        if any(not on_declared_simplex(p,shared,tolerance)for p in intersection):
            raise ValueError(f'triangles {i}/{j} intersect outside declared shared edge/vertex')
    return {'triangle_pairs_checked':checked,'declared_contacts':contacts,'unexpected_intersections':0,
            'coordinate_tolerance':tolerance,'algorithm':'triangle-plane segment contacts plus coplanar convex clipping; declared shared simplices only'}
