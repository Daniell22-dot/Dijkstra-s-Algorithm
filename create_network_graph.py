import ifcopenshell
import json
import os

ds = ifcopenshell.open('D:/deKUT-3D-Campus-Digital-Twin/src/data/bim/DANIEL.ifc')

# Get elements by type with floor information
all_elements = list(ds.by_type('IfcBuildingElement'))

# Define floor mapping
floor_mapping = {
    'Ground Floor': 'Ground',
    '1. Story': 'First',
    '2. Story': 'Second'
}

# Collect nodes for network graph
nodes = []
node_ids = set()

# Add staircase elements as nodes (critical for vertical navigation)
for stair in ds.by_type('IfcStair'):
    global_id = stair.GlobalId if hasattr(stair, 'GlobalId') else ''
    name = stair.Name if hasattr(stair, 'Name') else ''

    # Get floor from ContainedInStructure
    floor = 'Ground'
    if hasattr(stair, 'ContainedInStructure') and stair.ContainedInStructure:
        for rel in stair.ContainedInStructure:
            if rel and hasattr(rel, 'RelatingStructure'):
                rs = rel.RelatingStructure
                if rs and hasattr(rs, 'Name') and rs.Name in floor_mapping:
                    floor = floor_mapping[rs.Name]

    # Get Z coordinate
    z = 0
    if hasattr(stair, 'ObjectPlacement') and stair.ObjectPlacement:
        try:
            placement = stair.ObjectPlacement
            if hasattr(placement, 'RelativePlacement') and placement.RelativePlacement:
                rp = placement.RelativePlacement
                if hasattr(rp, 'PlacementOrigin') and rp.PlacementOrigin:
                    if hasattr(rp.PlacementOrigin, 'Coordinates'):
                        coords = rp.PlacementOrigin.Coordinates
                        if coords and len(coords) > 2:
                            z = coords[2]
        except:
            pass

    if global_id not in node_ids:
        node_ids.add(global_id)
        nodes.append({
            'id': global_id,
            'name': name[:50] if name else 'Stair_' + global_id,
            'floor': floor,
            'x': 0,
            'y': 0,
            'z': round(z, 2),
            'type': 'stair',
            'is_room': False
        })

# Add door elements as nodes (entry/exit points)
for door in ds.by_type('IfcDoor'):
    global_id = door.GlobalId if hasattr(door, 'GlobalId') else ''
    name = door.Name if hasattr(door, 'Name') else ''

    # Get floor
    floor = 'Ground'
    if hasattr(door, 'ContainedInStructure') and door.ContainedInStructure:
        for rel in door.ContainedInStructure:
            if rel and hasattr(rel, 'RelatingStructure'):
                rs = rel.RelatingStructure
                if rs and hasattr(rs, 'Name') and rs.Name in floor_mapping:
                    floor = floor_mapping[rs.Name]

    if global_id not in node_ids:
        node_ids.add(global_id)
        nodes.append({
            'id': global_id,
            'name': name[:50] if name else 'Door_' + global_id,
            'floor': floor,
            'x': 0,
            'y': 0,
            'z': 1.0,
            'type': 'door',
            'is_room': False
        })

# Add beam/column elements as potential room nodes (centers)
for elem in all_elements:
    if elem.is_a() in ['IfcColumn', 'IfcBeam']:
        global_id = elem.GlobalId if hasattr(elem, 'GlobalId') else ''
        name = elem.Name if hasattr(elem, 'Name') else ''
        etype = elem.is_a()

        # Get floor
        floor = 'Ground'
        if hasattr(elem, 'ContainedInStructure') and elem.ContainedInStructure:
            for rel in elem.ContainedInStructure:
                if rel and hasattr(rel, 'RelatingStructure'):
                    rs = rel.RelatingStructure
                    if rs and hasattr(rs, 'Name') and rs.Name in floor_mapping:
                        floor = floor_mapping[rs.Name]

        # Get Z coordinate
        z = 0
        if hasattr(elem, 'ObjectPlacement') and elem.ObjectPlacement:
            try:
                placement = elem.ObjectPlacement
                if hasattr(placement, 'RelativePlacement') and placement.RelativePlacement:
                    rp = placement.RelativePlacement
                    if hasattr(rp, 'PlacementOrigin') and rp.PlacementOrigin:
                        if hasattr(rp.PlacementOrigin, 'Coordinates'):
                            coords = rp.PlacementOrigin.Coordinates
                            if coords and len(coords) > 2:
                                z = coords[2]
            except:
                pass

        if global_id not in node_ids and len(nodes) < 500:
            node_ids.add(global_id)
            nodes.append({
                'id': global_id,
                'name': name[:30] if name else 'Space_' + global_id,
                'floor': floor,
                'x': 0,
                'y': 0,
                'z': round(z, 2),
                'type': etype.lower(),
                'is_room': True
            })

# Create edges based on spatial proximity and containment
# Elements on the same floor with nearby positions connect as corridors
edges = []

# Group nodes by floor
floor_groups = {}
for node in nodes:
    floor = node['floor']
    if floor not in floor_groups:
        floor_groups[floor] = []
    floor_groups[floor].append(node)

# Create edges within each floor (connect nearby elements)
for floor, floor_nodes in floor_groups.items():
    for i, node_a in enumerate(floor_nodes):
        for node_b in floor_nodes[i+1:i+5]:
            if node_a['id'] != node_b['id']:
                weight = 1.0
                edges.append({
                    'from': node_a['id'],
                    'to': node_b['id'],
                    'weight': weight,
                    'floor': floor,
                    'type': 'corridor'
                })

# Also add edges between connected stairs (vertical movement)
for i, stair1 in enumerate(nodes):
    if stair1['type'] == 'stair':
        for j, stair2 in enumerate(nodes):
            if i != j and stair2['type'] == 'stair' and stair1['floor'] != stair2['floor']:
                weight = 2.0
                edges.append({
                    'from': stair1['id'],
                    'to': stair2['id'],
                    'weight': weight,
                    'floor': 'Transition',
                    'type': 'staircase'
                })

# Create the network graph
network_graph = {
    'nodes': nodes,
    'edges': edges
}

# Write JSON file
output_path = 'src/data/routing/network_graph.json'
os.makedirs(os.path.dirname(output_path), exist_ok=True)
with open(output_path, 'w', encoding='utf-8') as f:
    json.dump(network_graph, f, indent=2)

print('Network graph created:')
print('  Nodes: ' + str(len(nodes)))
print('  Edges: ' + str(len(edges)))
print('  Floors: ' + str(list(floor_groups.keys())))
print('Sample nodes:')
for n in nodes[:5]:
    print('  ' + n['id'] + ': ' + n['name'] + ' | Floor: ' + n['floor'] + ' | Type: ' + n['type'] + ' | Z: ' + str(n['z']))
print('Sample edges:')
for e in edges[:5]:
    print('  ' + e['from'] + ' -> ' + e['to'] + ' | Floor: ' + e['floor'] + ' | Type: ' + e['type'] + ' | Weight: ' + str(e['weight']))