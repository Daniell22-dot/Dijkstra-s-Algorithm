import ifcopenshell
import os

ds = ifcopenshell.open('D:/deKUT-3D-Campus-Digital-Twin/src/data/bim/DANIEL.ifc')
all_elements = list(ds.by_type('IfcBuildingElement'))

# Check all elements for floor/level information
print('=== Element Floor/Level Analysis ===')
floor_z_map = {}

for elem in all_elements:
    gid = elem.GlobalId if hasattr(elem, 'GlobalId') else ''
    name = elem.Name if hasattr(elem, 'Name') else ''
    etype = elem.is_a()
    
    # Check ContainedInStructure for spatial assignment
    floor_name = ''
    if hasattr(elem, 'ContainedInStructure') and elem.ContainedInStructure:
        for rel in elem.ContainedInStructure:
            if rel and hasattr(rel, 'RelatingStructure'):
                rs = rel.RelatingStructure
                if rs and hasattr(rs, 'Name'):
                    floor_name = rs.Name
    
    # Check ObjectPlacement for Z coordinate
    z_coord = 0
    if hasattr(elem, 'ObjectPlacement') and elem.ObjectPlacement:
        try:
            placement = elem.ObjectPlacement
            # Try different placement types
            if hasattr(placement, 'RelativePlacement') and placement.RelativePlacement:
                rp = placement.RelativePlacement
                # IfcAxis2Placement.Linear or IfcAxis2Placement3D
                if hasattr(rp, 'PlacementOrigin') and rp.PlacementOrigin:
                    if hasattr(rp.PlacementOrigin, 'Coordinates'):
                        coords = rp.PlacementOrigin.Coordinates
                        if coords and len(coords) > 2:
                            z_coord = coords[2]
                elif hasattr(rp, 'Location') and rp.Location:
                    if hasattr(rp.Location, 'Coordinates'):
                        coords = rp.Location.Coordinates
                        if coords and len(coords) > 2:
                            z_coord = coords[2]
            elif hasattr(placement, 'Location') and placement.Location:
                if hasattr(placement.Location, 'Coordinates'):
                    coords = placement.Location.Coordinates
                    if coords and len(coords) > 2:
                        z_coord = coords[2]
        except Exception as e:
            pass
    
    floor_key = floor_name if floor_name else 'Unassigned'
    if floor_key not in floor_z_map:
        floor_z_map[floor_key] = []
    floor_z_map[floor_key].append({
        'global_id': gid,
        'name': name[:30] if name else '',
        'type': etype,
        'z': z_coord
    })

# Print floors sorted by Z coordinate
for floor in sorted(floor_z_map.keys(), key=lambda f: min([e.get('z', 0) for e in floor_z_map[f]])):
    elements = floor_z_map[floor]
    z_values = [e['z'] for e in elements]
    print(f'{floor}: {len(elements)} elements, Z range: {min(z_values):.2f} to {max(z_values):.2f}')
    for e in elements[:3]:
        print(f'  {e["type"]}: {e["name"]} Z={e["z"]:.2f}')
    if len(elements) > 3:
        print(f'  ... and {len(elements)-3} more')