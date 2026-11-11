"""
Extract BIM data from IFC files into CSV files and a routing network graph.

Rooms are taken from IfcSpace (not from windows/columns like the old scripts),
so room names/types match the labels authored in ArchiCAD.

Usage:
    python extract_ifc_data.py [path/to/model.ifc]

Defaults to src/data/bim/DANIEL.ifc and writes:
    src/data/bim/rooms.csv
    src/data/bim/doors.csv
    src/data/bim/windows.csv
    src/data/bim/floors.csv
    src/data/routing/network_graph.json
"""

import argparse
import csv
import json
import math
import os
import sys

import ifcopenshell
import ifcopenshell.geom as geom
import ifcopenshell.util.element as element_util
import ifcopenshell.util.placement as placement_util
import ifcopenshell.util.unit as unit_util

ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_IFC = os.path.join(ROOT, 'src', 'data', 'bim', 'DANIEL.ifc')
BIM_OUT = os.path.join(ROOT, 'src', 'data', 'bim')
ROUTING_OUT = os.path.join(ROOT, 'src', 'data', 'routing')

FLOOR_MAP = {
    'ground floor': 'Ground',
    'ground': 'Ground',
    '0': 'Ground',
    '1. story': 'First',
    '1st story': 'First',
    'first': 'First',
    '2. story': 'Second',
    '2nd story': 'Second',
    'second': 'Second',
    '3. story': 'Third',
    'third': 'Third',
    '4': 'Fourth',
    '5': 'Fifth',
}

ROOM_FIELDS = [
    'id', 'name', 'floor', 'type', 'area', 'capacity', 'equipment',
    'year_built', 'maintenance_status', 'risk_level',
    'temperature', 'noise_db', 'lighting_lux',
    'latitude', 'longitude', 'center_x', 'center_y', 'center_z',
]
ELEMENT_FIELDS = ['id', 'name', 'floor', 'width', 'height', 'material', 'status']
FLOOR_FIELDS = ['id', 'name', 'level', 'area', 'material', 'status']


def floor_name(storey):
    if storey is None:
        return 'Ground'
    raw = (storey.Name or '').strip()
    key = raw.lower()
    if key in FLOOR_MAP:
        return FLOOR_MAP[key]
    if 'ground' in key:
        return 'Ground'
    if 'first' in key or key.startswith('1'):
        return 'First'
    if 'second' in key or key.startswith('2'):
        return 'Second'
    if 'third' in key or key.startswith('3'):
        return 'Third'
    return raw or 'Ground'


def get_storey(element):
    for rel in getattr(element, 'ContainedInStructure', None) or []:
        structure = getattr(rel, 'RelatingStructure', None)
        if structure is not None and structure.is_a('IfcBuildingStorey'):
            return structure
    for rel in getattr(element, 'Decomposes', None) or []:
        parent = getattr(rel, 'RelatingObject', None)
        if parent is not None and parent.is_a('IfcBuildingStorey'):
            return parent
    return None


def get_material_name(element):
    try:
        material = element_util.get_material(element)
        if material is None:
            return None
        return getattr(material, 'Name', None)
    except Exception:
        return None


class Geometry:
    def __init__(self, ifc_file):
        self.settings = geom.settings()
        self.settings.set(self.settings.USE_WORLD_COORDS, True)
        try:
            self.unit_scale = unit_util.calculate_unit_scale(ifc_file)
        except Exception:
            self.unit_scale = 1.0

    def shape_points(self, element):
        shape = geom.create_shape(self.settings, element)
        verts = shape.geometry.verts
        return [(verts[i], verts[i + 1], verts[i + 2]) for i in range(0, len(verts), 3)]

    def placement_center(self, element):
        try:
            matrix = placement_util.get_local_placement(element.ObjectPlacement)
            return (
                float(matrix[0][3]) * self.unit_scale,
                float(matrix[1][3]) * self.unit_scale,
                float(matrix[2][3]) * self.unit_scale,
            )
        except Exception:
            return None

    def space_metrics(self, space):
        """Return (area_m2, center_x, center_y, floor_z) in metres."""
        try:
            points = self.shape_points(space)
        except Exception:
            points = []
        if not points:
            center = self.placement_center(space)
            return 0.0, *(center or (0.0, 0.0, 0.0))

        min_z = min(p[2] for p in points)
        try:
            shape = geom.create_shape(self.settings, space)
            faces = shape.geometry.faces
            floor_triangles = []
            area = 0.0
            for i in range(0, len(faces), 3):
                tri = [points[faces[i]], points[faces[i + 1]], points[faces[i + 2]]]
                if all(abs(p[2] - min_z) <= 0.05 for p in tri):
                    (x1, y1, _), (x2, y2, _), (x3, y3, _) = tri
                    tri_area = abs((x2 - x1) * (y3 - y1) - (x3 - x1) * (y2 - y1)) / 2.0
                    if tri_area > 1e-9:
                        area += tri_area
                        floor_triangles.extend(tri)
            if floor_triangles:
                cx = sum(p[0] for p in floor_triangles) / len(floor_triangles)
                cy = sum(p[1] for p in floor_triangles) / len(floor_triangles)
            else:
                cx = sum(p[0] for p in points) / len(points)
                cy = sum(p[1] for p in points) / len(points)
            if area <= 1e-6:
                xs = [p[0] for p in points]
                ys = [p[1] for p in points]
                area = (max(xs) - min(xs)) * (max(ys) - min(ys))
            return area, cx, cy, min_z
        except Exception:
            cx = sum(p[0] for p in points) / len(points)
            cy = sum(p[1] for p in points) / len(points)
            return 0.0, cx, cy, min_z

    def element_center(self, element):
        try:
            points = self.shape_points(element)
            if points:
                return (
                    sum(p[0] for p in points) / len(points),
                    sum(p[1] for p in points) / len(points),
                    sum(p[2] for p in points) / len(points),
                )
        except Exception:
            pass
        return self.placement_center(element) or (0.0, 0.0, 0.0)

    def length(self, value):
        if value is None:
            return None
        return round(float(value) * self.unit_scale, 3)


def extract_rooms(ifc_file, geometry):
    rooms = []
    for space in ifc_file.by_type('IfcSpace'):
        storey = get_storey(space)
        area, cx, cy, cz = geometry.space_metrics(space)
        name = (space.Name or '').strip() or f'Space {space.GlobalId[-4:]}'
        room_type = (space.LongName or '').strip() or 'Space'
        rooms.append({
            'id': space.GlobalId,
            'name': name,
            'floor': floor_name(storey),
            'type': room_type,
            'area': round(area, 2),
            'capacity': None,
            'equipment': None,
            'year_built': None,
            'maintenance_status': 'Good',
            'risk_level': 'Low',
            'temperature': None,
            'noise_db': None,
            'lighting_lux': None,
            'latitude': None,
            'longitude': None,
            'center_x': round(cx, 3),
            'center_y': round(cy, 3),
            'center_z': round(cz, 3),
        })
    return rooms


def extract_elements(ifc_file, geometry, ifc_type):
    rows = []
    for element in ifc_file.by_type(ifc_type):
        storey = get_storey(element)
        cx, cy, cz = geometry.element_center(element)
        rows.append({
            'id': element.GlobalId,
            'name': (element.Name or '').strip() or element.GlobalId,
            'floor': floor_name(storey),
            'width': geometry.length(getattr(element, 'OverallWidth', None)),
            'height': geometry.length(getattr(element, 'OverallHeight', None)),
            'material': get_material_name(element),
            'status': 'Good',
            '_center': (cx, cy, cz),
        })
    return rows


def extract_floors(ifc_file, geometry, rooms):
    storeys = sorted(
        ifc_file.by_type('IfcBuildingStorey'),
        key=lambda s: (s.Elevation if s.Elevation is not None else 0.0),
    )
    area_by_floor = {}
    for room in rooms:
        area_by_floor[room['floor']] = area_by_floor.get(room['floor'], 0.0) + (room['area'] or 0.0)
    floors = []
    for level, storey in enumerate(storeys):
        mapped = floor_name(storey)
        floors.append({
            'id': storey.GlobalId,
            'name': mapped,
            'level': level,
            'area': round(area_by_floor.get(mapped, 0.0), 2),
            'material': 'Concrete',
            'status': 'Good',
        })
    return floors


class DSU:
    def __init__(self):
        self.parent = {}

    def find(self, item):
        self.parent.setdefault(item, item)
        while self.parent[item] != item:
            self.parent[item] = self.parent[self.parent[item]]
            item = self.parent[item]
        return item

    def union(self, a, b):
        ra, rb = self.find(a), self.find(b)
        if ra == rb:
            return False
        self.parent[rb] = ra
        return True


def distance(a, b):
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2)


def build_network(ifc_file, geometry, rooms, doors, stairs, floors):
    nodes = []
    node_by_id = {}
    global_dsu = DSU()

    for room in rooms:
        node = {
            'id': room['id'],
            'name': room['name'],
            'floor': room['floor'],
            'x': room['center_x'],
            'y': room['center_y'],
            'z': room['center_z'],
            'type': room['type'],
            'is_room': True,
        }
        nodes.append(node)
        node_by_id[node['id']] = node

    for element in doors:
        cx, cy, cz = element['_center']
        node = {
            'id': element['id'],
            'name': element['name'],
            'floor': element['floor'],
            'x': round(cx, 3),
            'y': round(cy, 3),
            'z': round(cz, 3),
            'type': 'door',
            'is_room': False,
        }
        nodes.append(node)
        node_by_id[node['id']] = node

    for element in stairs:
        cx, cy, cz = element['_center']
        node = {
            'id': element['id'],
            'name': element['name'],
            'floor': element['floor'],
            'x': round(cx, 3),
            'y': round(cy, 3),
            'z': round(cz, 3),
            'type': 'stair',
            'is_room': False,
        }
        nodes.append(node)
        node_by_id[node['id']] = node

    edges = []
    edge_keys = set()

    def add_edge(a, b, edge_type, floor=None):
        if a == b:
            return
        key = tuple(sorted((a, b)))
        if key in edge_keys:
            return
        edge_keys.add(key)
        global_dsu.union(a, b)
        na, nb = node_by_id[a], node_by_id[b]
        edges.append({
            'from': a,
            'to': b,
            'weight': round(distance(
                (na['x'], na['y'], na['z']),
                (nb['x'], nb['y'], nb['z']),
            ), 3),
            'floor': floor or na['floor'],
            'type': edge_type,
        })

    by_floor = {}
    for node in nodes:
        by_floor.setdefault(node['floor'], []).append(node)

    for node in nodes:
        if node['type'] != 'door':
            continue
        candidates = sorted(
            (n for n in by_floor.get(node['floor'], []) if n['is_room']),
            key=lambda n: distance(
                (node['x'], node['y'], node['z']),
                (n['x'], n['y'], n['z']),
            ),
        )
        for candidate in candidates[:2]:
            add_edge(node['id'], candidate['id'], 'door', node['floor'])

    for node in nodes:
        if node['type'] != 'Corridor':
            continue
        candidates = sorted(
            (n for n in by_floor.get(node['floor'], [])
             if n['is_room'] and n['type'] == 'Corridor' and n['id'] != node['id']),
            key=lambda n: distance(
                (node['x'], node['y'], node['z']),
                (n['x'], n['y'], n['z']),
            ),
        )
        for candidate in candidates[:3]:
            add_edge(node['id'], candidate['id'], 'corridor', node['floor'])

    # Guarantee every floor is connected: Kruskal spanning tree per floor.
    for floor, floor_nodes in by_floor.items():
        if len(floor_nodes) < 2:
            continue
        pairs = []
        for i, a in enumerate(floor_nodes):
            for b in floor_nodes[i + 1:]:
                pairs.append((
                    distance((a['x'], a['y'], a['z']), (b['x'], b['y'], b['z'])),
                    a['id'],
                    b['id'],
                ))
        pairs.sort(key=lambda p: p[0])
        dsu = DSU()
        for _, a, b in pairs:
            if dsu.union(a, b):
                add_edge(a, b, 'corridor', floor)

    # Connect stairwells across floors.
    stairs_by_floor = {}
    for node in nodes:
        if node['type'] == 'stair':
            stairs_by_floor.setdefault(node['floor'], []).append(node)
    floor_order = [floor['name'] for floor in sorted(floors, key=lambda f: f['level'])]
    floor_order = [floor for floor in floor_order if floor in by_floor]

    for floor in floor_order:
        for stair in stairs_by_floor.get(floor, []):
            for other_floor in floor_order:
                if other_floor == floor:
                    continue
                others = stairs_by_floor.get(other_floor, [])
                if not others:
                    continue
                nearest = min(
                    others,
                    key=lambda n: distance(
                        (stair['x'], stair['y'], stair['z']),
                        (n['x'], n['y'], n['z']),
                    ),
                )
                add_edge(stair['id'], nearest['id'], 'stair', 'Transition')

    # Floors without stair elements (e.g. the Second floor in this model) still
    # need a vertical link. Join each consecutive floor at the closest XY point.
    for lower, upper in zip(floor_order, floor_order[1:]):
        lower_nodes = by_floor[lower]
        upper_nodes = by_floor[upper]
        if global_dsu.find(lower_nodes[0]['id']) == global_dsu.find(upper_nodes[0]['id']):
            continue
        best = None
        for a in lower_nodes:
            for b in upper_nodes:
                xy_distance = math.hypot(a['x'] - b['x'], a['y'] - b['y'])
                if best is None or xy_distance < best[0]:
                    best = (xy_distance, a['id'], b['id'])
        if best is not None:
            add_edge(best[1], best[2], 'stair', 'Transition')

    return {
        'building': os.path.splitext(os.path.basename(ifc_file_path))[0],
        'units': 'metres',
        'nodes': nodes,
        'edges': edges,
        'floors': floor_order,
    }


def write_csv(path, fields, rows):
    with open(path, 'w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    print(f'  wrote {len(rows):>4} rows -> {os.path.relpath(path, ROOT)}')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('ifc', nargs='?', default=DEFAULT_IFC)
    args = parser.parse_args()

    global ifc_file_path
    ifc_file_path = os.path.abspath(args.ifc)
    if not os.path.exists(ifc_file_path):
        sys.exit(f'IFC file not found: {ifc_file_path}')

    print(f'Opening {ifc_file_path}')
    ifc_file = ifcopenshell.open(ifc_file_path)
    geometry = Geometry(ifc_file)

    rooms = extract_rooms(ifc_file, geometry)
    doors = extract_elements(ifc_file, geometry, 'IfcDoor')
    windows = extract_elements(ifc_file, geometry, 'IfcWindow')
    stairs = extract_elements(ifc_file, geometry, 'IfcStair')
    floors = extract_floors(ifc_file, geometry, rooms)

    network = build_network(ifc_file, geometry, rooms, doors, stairs, floors)

    os.makedirs(BIM_OUT, exist_ok=True)
    os.makedirs(ROUTING_OUT, exist_ok=True)

    print('\nWriting extracted data')
    write_csv(os.path.join(BIM_OUT, 'rooms.csv'), ROOM_FIELDS, rooms)
    write_csv(os.path.join(BIM_OUT, 'doors.csv'), ELEMENT_FIELDS, doors)
    write_csv(os.path.join(BIM_OUT, 'windows.csv'), ELEMENT_FIELDS, windows)
    write_csv(os.path.join(BIM_OUT, 'floors.csv'), FLOOR_FIELDS, floors)
    with open(os.path.join(ROUTING_OUT, 'network_graph.json'), 'w', encoding='utf-8') as handle:
        json.dump(network, handle, indent=2)
    print(f'  wrote {len(network["nodes"]):>4} nodes / {len(network["edges"]):>4} edges -> '
          f'src/data/routing/network_graph.json')

    floor_counts = {}
    for room in rooms:
        floor_counts[room['floor']] = floor_counts.get(room['floor'], 0) + 1
    print('\nSummary')
    print(f'  rooms:   {len(rooms)} {floor_counts}')
    print(f'  doors:   {len(doors)}')
    print(f'  windows: {len(windows)}')
    print(f'  floors:  {len(floors)}')
    print(f'  nodes:   {len(network["nodes"])}')
    print(f'  edges:   {len(network["edges"])}')


if __name__ == '__main__':
    main()
