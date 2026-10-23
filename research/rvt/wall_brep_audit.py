"""Independent planar native-BRep loop, manifold and volume measurements.

Consumes decoded native graph fields, never wall-driver dimensions or IFC meshes.
Only single closed convex planar loops are supported; open sheet Geometry
objects are reported separately from closed solids.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

TOL = 1e-8


def sub(a, b): return [x-y for x, y in zip(a, b)]
def dot(a, b): return sum(x*y for x, y in zip(a, b))
def cross(a, b): return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]
def norm(a): return math.sqrt(dot(a, a))
def close(a, b): return norm(sub(a, b)) <= TOL


def resolver(graph):
    objects = graph['objects']; tokens = {}
    for i, obj in enumerate(objects):
        token = obj['token']
        if token not in (0, 0xffffffff):
            if token in tokens: raise ValueError('duplicate graph token')
            tokens[token] = i
    edges = {}
    for edge in graph['edges']:
        offset = edge['pointer_offset']
        if offset in edges: raise ValueError('duplicate owning pointer offset')
        edges[offset] = edge['target_object_index']
    def resolve(pointer):
        if pointer['pointer_token'] == 0: return None
        index = edges.get(pointer['offset']) if pointer['class_tag'] is not None else tokens.get(pointer['pointer_token'])
        if index is None or not 0 <= index < len(objects): raise ValueError('unresolved BRep pointer')
        return index
    return resolve


def face_polygon(graph, face_index, resolve):
    objects = graph['objects']; face = objects[face_index]['fields']
    if face['m_faceRegions']: raise ValueError('face regions unsupported')
    plane_index = resolve(face['m_pSurf'])
    if plane_index is None or objects[plane_index]['class_name'] != 'Plane': raise ValueError('nonplanar face')
    plane = objects[plane_index]['fields']
    origin, x, y = [plane[k] for k in ('m_origin', 'm_xVec', 'm_yVec')]
    if any(len(v) != 3 or any(not math.isfinite(t) for t in v) for v in (origin, x, y)):
        raise ValueError('nonfinite plane')
    if abs(norm(x)-1) > TOL or abs(norm(y)-1) > TOL or abs(dot(x, y)) > TOL:
        raise ValueError('nonorthonormal plane')
    loop_index = resolve(face['m_pFirstLoop'])
    if loop_index is None or objects[loop_index]['class_name'] != 'EdgeLoop': raise ValueError('missing face loop')
    loop = objects[loop_index]['fields']
    if loop['m_open'] or resolve(loop['m_nextLoop']) is not None or resolve(loop['m_pFace']) != face_index:
        raise ValueError('unsupported face loop ownership or holes')
    current = resolve(loop['m_next']); previous = loop_index; used = []; endpoints = []
    while current != loop_index:
        if current is None or current in used or len(used) >= len(objects) or objects[current]['class_name'] != 'Edge':
            raise ValueError('broken edge-loop cycle')
        fields = objects[current]['fields']
        sides = [i for i, p in enumerate(fields['m_pFace']) if resolve(p) == face_index]
        if len(sides) != 1: raise ValueError('edge-face incidence mismatch')
        side = sides[0]
        if resolve(fields['m_prev'][side]) != previous: raise ValueError('edge-loop previous link mismatch')
        if fields['m_interiorEdgePnts'] or len(fields['m_firstAndLastEdgePnts']) != 2:
            raise ValueError('nonlinear edge unsupported')
        points = []
        for endpoint in fields['m_firstAndLastEdgePnts']:
            uv = endpoint['uv'][side]
            if len(uv) != 2 or any(not math.isfinite(t) for t in uv): raise ValueError('nonfinite UV')
            points.append([origin[j]+uv[0]*x[j]+uv[1]*y[j] for j in range(3)])
        if close(*points): raise ValueError('degenerate edge')
        endpoints.append(points); used.append(current)
        previous, current = current, resolve(fields['m_next'][side])
    if len(used) < 3 or resolve(loop['m_prev']) != used[-1]: raise ValueError('incomplete face loop')
    polygons = []
    for first in (endpoints[0], endpoints[0][::-1]):
        polygon = [first[0]]; last = first[1]; valid = True
        for pair in endpoints[1:]:
            if close(last, pair[0]): begin, finish = pair
            elif close(last, pair[1]): begin, finish = pair[::-1]
            else: valid = False; break
            polygon.append(begin); last = finish
        if valid and close(last, polygon[0]): polygons.append(polygon)
    if len(polygons) != 1: raise ValueError('disconnected or ambiguous loop endpoints')
    polygon = polygons[0]; normal = cross(x, y)
    signs = [dot(cross(sub(polygon[(i+1)%len(polygon)], p), sub(polygon[(i+2)%len(polygon)], polygon[(i+1)%len(polygon)])), normal) for i, p in enumerate(polygon)]
    if any(abs(v) <= TOL for v in signs) or not (all(v > 0 for v in signs) or all(v < 0 for v in signs)):
        raise ValueError('nonconvex or degenerate face loop')
    if any(abs(dot(sub(p, origin), normal)) > TOL for p in polygon): raise ValueError('nonplanar polygon')
    return polygon, used, {'face_object': face_index, 'plane_object': plane_index,
        'loop_object': loop_index, 'edges': used,
        'loop_orientation_against_plane_basis': 1 if signs[0] > 0 else -1,
        'stored_plane_orient_flag': plane['m_orientFlag']}


def audit_graph(graph):
    objects = graph['objects']; resolve = resolver(graph); geometries = []
    for geometry_index, obj in enumerate(objects):
        if obj['class_name'] != 'Geometry': continue
        face_indices = [resolve(p) for p in obj['fields']['m_pFaces']]
        edge_indices = [resolve(p) for p in obj['fields']['m_pEdges']]
        if None in face_indices or len(set(face_indices)) != len(face_indices) or len(set(edge_indices)) != len(edge_indices):
            raise ValueError('invalid geometry ownership')
        polygons = []; face_reports = []; used_edges = []
        for face in face_indices:
            if objects[face]['class_name'] != 'Face': raise ValueError('geometry owns non-face')
            polygon, used, report = face_polygon(graph, face, resolve)
            polygons.append(polygon); used_edges.extend(used); face_reports.append(report)
        if set(used_edges) != set(edge_indices): raise ValueError('geometry edge collection differs from loops')
        vertices = []
        def vertex_id(point):
            matches = [i for i, existing in enumerate(vertices) if close(point, existing)]
            if len(matches) > 1: raise ValueError('ambiguous vertex merge tolerance')
            if matches: return matches[0]
            vertices.append(point); return len(vertices)-1
        polygons_ids = [[vertex_id(p) for p in polygon] for polygon in polygons]
        directed = Counter((a, b) for ids in polygons_ids for a, b in zip(ids, ids[1:]+ids[:1]))
        unordered = Counter(tuple(sorted(edge)) for edge in directed.elements())
        if any(count > 2 for count in unordered.values()): raise ValueError('nonmanifold edge incidence')
        boundary = sum(count == 1 for count in unordered.values())
        closed = boundary == 0
        if closed and any(directed[(b, a)] != count for (a, b), count in directed.items()):
            raise ValueError('closed BRep face winding is inconsistent')
        center = [sum(p[i] for p in vertices)/len(vertices) for i in range(3)]
        signed_volume = 0.; area = 0.
        for polygon in polygons:
            base = sub(polygon[0], center)
            for i in range(1, len(polygon)-1):
                a, b = sub(polygon[i], center), sub(polygon[i+1], center)
                signed_volume += dot(base, cross(a, b))/6
                area += norm(cross(sub(polygon[i], polygon[0]), sub(polygon[i+1], polygon[0])))/2
        if closed and abs(signed_volume) <= TOL: raise ValueError('closed BRep has zero volume')
        if closed:
            orientation = 1 if signed_volume > 0 else -1
            for polygon in polygons:
                outward = [orientation*t for t in cross(sub(polygon[1], polygon[0]), sub(polygon[2], polygon[0]))]
                unit = [t/norm(outward) for t in outward]
                if any(dot(sub(vertex, polygon[0]), unit) > TOL for vertex in vertices):
                    raise ValueError('closed BRep is not a convex consistently oriented solid')
        geometries.append({'geometry_object': geometry_index, 'faces': len(polygons), 'edges': len(unordered),
            'vertices': len(vertices), 'boundary_edges': boundary, 'closed': closed,
            'euler_characteristic': len(vertices)-len(unordered)+len(polygons),
            'surface_area_square_feet': area, 'signed_volume_cubic_feet': signed_volume if closed else None,
            'volume_cubic_feet': abs(signed_volume) if closed else None,
            'bounds_feet': [[min(p[i] for p in vertices) for i in range(3)], [max(p[i] for p in vertices) for i in range(3)]],
            'face_loops': face_reports})
    if not geometries: raise ValueError('no native Geometry objects')
    union = [[min(g['bounds_feet'][0][i] for g in geometries) for i in range(3)],
             [max(g['bounds_feet'][1][i] for g in geometries) for i in range(3)]]
    root = objects[0]
    if root['class_name'] != 'GElement': raise ValueError('expected GElement root')
    for key in ('m_bBox', 'm_tightbBox'):
        saved = root['fields'][key]
        if len(saved) != 2 or any(len(p) != 3 or any(not math.isfinite(t) for t in p) for p in saved):
            raise ValueError('nonfinite native bounding box')
        if any(not close(saved[i], union[i]) for i in range(2)):
            raise ValueError('saved native bounding box differs from BRep vertices')
    return {'native_vertex_bounds_feet': union, 'saved_root_bounds_match_native_vertices': True,
        'geometry_components': geometries, 'closed_solids': sum(g['closed'] for g in geometries),
        'closed_solid_volume_cubic_feet': sum(g['volume_cubic_feet'] or 0 for g in geometries),
        'limitations': ['Convex single-loop planar faces only; holes, curved edges and regions rejected.',
            'Stored orientation flag semantics are reported, not assumed.',
            'Closed manifold geometry alone does not establish native Revit acceptance.']}


def audit_saved_decode(path, candidate):
    data = path.read_bytes(); decoded = json.loads(data)
    actual_sha = hashlib.sha256(candidate.read_bytes()).hexdigest()
    if decoded['candidate_sha256'] != actual_sha:
        raise ValueError('candidate hash differs from independent decode')
    from schema_probe import REV
    if decoded['reader_revision'] != REV:
        raise ValueError('reader revision differs')
    records = [record for record in decoded['records'] if record['channel'] == 103]
    if len(records) != 1 or records[0]['graph']['consumed_bytes'] != records[0]['source']['body_bytes']:
        raise ValueError('expected one complete channel103 graph')
    record = records[0]
    audit = audit_graph(record['graph'])
    headers = [r for r in decoded['records'] if r['channel'] == 101]
    if len(headers) != 1 or headers[0]['graph']['consumed_bytes'] != headers[0]['source']['body_bytes']:
        raise ValueError('expected one complete header graph')
    outlines = [o['fields']['m_minmax'] for o in headers[0]['graph']['objects'] if o['class_name'] == 'Outline']
    if len(outlines) != 1 or any(not close(outlines[0][i], audit['native_vertex_bounds_feet'][i]) for i in range(2)):
        raise ValueError('header Outline differs from native vertices')
    audit['header_outline_matches_native_vertices'] = True
    return {'candidate_sha256': actual_sha, 'reader_revision': REV,
        'independent_decode_json_sha256': hashlib.sha256(data).hexdigest(),
        'probe_binary_sha256': decoded['probe_binary_sha256'],
        'probe_source_sha256': decoded['probe_source_sha256'],
        'native_record_source': record['source'], 'element_id': record['identity']['element_id'],
        **audit}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__); p.add_argument('graph', type=Path)
    p.add_argument('--candidate', type=Path)
    a = p.parse_args()
    if a.candidate:
        result = audit_saved_decode(a.graph, a.candidate)
    else:
        data = a.graph.read_bytes(); value = json.loads(data)
        graph = value['graphs']['103'] if 'graphs' in value else value['103'] if '103' in value else value
        result = {'graph_sha256': hashlib.sha256(data).hexdigest(), **audit_graph(graph)}
    print(json.dumps(result, indent=2))
