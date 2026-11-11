import ifcopenshell
import csv
import os

ds = ifcopenshell.open('D:/deKUT-3D-Campus-Digital-Twin/src/data/bim/DANIEL.ifc')

# Get all building elements
all_elements = list(ds.by_type('IfcBuildingElement'))

# Define floor mapping from IFC story names to database floor values
floor_mapping = {
    'Ground Floor': 'Ground',
    '1. Story': 'First',
    '2. Story': 'Second'
}

# Get elements grouped by floor
elements_by_floor = {'Ground': [], 'First': [], 'Second': []}

for elem in all_elements:
    global_id = elem.GlobalId if hasattr(elem, 'GlobalId') else ''
    name = elem.Name if hasattr(elem, 'Name') else ''
    etype = elem.is_a()
    
    # Determine floor from ContainedInStructure
    floor_db = 'Ground'  # default
    if hasattr(elem, 'ContainedInStructure') and elem.ContainedInStructure:
        for rel in elem.ContainedInStructure:
            if rel and hasattr(rel, 'RelatingStructure'):
                rs = rel.RelatingStructure
                if rs and hasattr(rs, 'Name'):
                    floor_name = rs.Name
                    if floor_name in floor_mapping:
                        floor_db = floor_mapping[floor_name]
                    else:
                        # Try to map based on name patterns
                        if any(kw in floor_name.upper() for kw in ['GROUND', 'GROUND FLOOR', 'LOWER']):
                            floor_db = 'Ground'
                        elif any(kw in floor_name.upper() for kw in ['FIRST', '1ST', 'UPPER']):
                            floor_db = 'First'
                        elif any(kw in floor_name.upper() for kw in ['SECOND', '2ND', 'UPPER2']):
                            floor_db = 'Second'
    
    # Only add if not already processed
    key = (floor_db, global_id)
    if key not in [(e['floor'], e.get('id')) for floor_list in elements_by_floor.values() for e in floor_list]:
        elements_by_floor[floor_db].append({
            'id': global_id,
            'name': name[:50] if name else f'Element_{global_id}',
            'type': etype,
            'floor': floor_db
        })

# Print summary
print('Elements by floor:')
for floor, elems in elements_by_floor.items():
    print(f'  {floor}: {len(elems)} elements')

# Now create rooms CSV with proper floor distribution
rooms = []
processed_ids = set()

# Add rooms from columns and beams on each floor
for floor, prefix in [('Ground', 'CRE'), ('First', 'BMR'), ('Second', 'BMR')]:
    # Get elements for this floor
    floor_elements = [e for e in all_elements 
                      if e.is_a() in ['IfcColumn', 'IfcBeam'] 
                      and hasattr(e, 'ContainedInStructure')]
    
    # Assign to floor based on ContainedInStructure
    for elem in floor_elements:
        global_id = elem.GlobalId if hasattr(elem, 'GlobalId') else ''
        name = elem.Name if hasattr(elem, 'Name') else ''
        obj_type = elem.ObjectType if hasattr(elem, 'ObjectType') else ''
        
        if global_id in processed_ids:
            continue
        processed_ids.add(global_id)
        
        # Determine floor
        floor_db = 'Ground'
        if hasattr(elem, 'ContainedInStructure') and elem.ContainedInStructure:
            for rel in elem.ContainedInStructure:
                if rel and hasattr(rel, 'RelatingStructure'):
                    rs = rel.RelatingStructure
                    if rs and hasattr(rs, 'Name') and rs.Name in floor_mapping:
                        floor_db = floor_mapping[rs.Name]
                    elif rs.Name == '1. Story':
                        floor_db = 'First'
                    elif rs.Name == '2. Story':
                        floor_db = 'Second'
        
        # Extract Z coordinate for center_z
        center_z = 0
        if hasattr(elem, 'ObjectPlacement') and elem.ObjectPlacement:
            try:
                placement = elem.ObjectPlacement
                if hasattr(placement, 'RelativePlacement') and placement.RelativePlacement:
                    rp = placement.RelativePlacement
                    if hasattr(rp, 'PlacementOrigin') and rp.PlacementOrigin:
                        if hasattr(rp.PlacementOrigin, 'Coordinates'):
                            coords = rp.PlacementOrigin.Coordinates
                            if coords and len(coords) > 2:
                                center_z = coords[2]
            except:
                pass
        
        # Estimate area based on element type
        area = 0
        if etype == 'IfcColumn':
            area = 4.0  # typical column area
        elif etype == 'IfcBeam':
            area = 3.0  # typical beam area
        
        rooms.append({
            'id': global_id,
            'name': name[:50] if name else f'Room_{global_id}',
            'floor': floor_db,
            'type': etype,
            'area': round(area, 2),
            'capacity': 20 if floor_db == 'Ground' else 15,
            'equipment': '',
            'year_built': None,
            'maintenance_status': 'Good',
            'risk_level': 'Low',
            'temperature': None,
            'noise_db': None,
            'lighting_lux': None,
            'latitude': None,
            'longitude': None,
            'center_x': 0,
            'center_y': 0,
            'center_z': round(center_z, 2)
        })

# Also add some rooms based on the building naming convention
# The IFC file has elements like "BMR - 074" (Building Model Room), "CRE - 001" (Core)
for floor_name, floor_key in [('Ground', 'Ground'), ('First', 'First'), ('Second', 'Second')]:
    # Add rooms based on naming patterns found in the IFC
    floor_elements = [e for e in all_elements 
                      if hasattr(e, 'ContainedInStructure')]
    
    for elem in floor_elements[:20]:  # Limit per floor
        global_id = elem.GlobalId if hasattr(elem, 'GlobalId') else ''
        name = elem.Name if hasattr(elem, 'Name') else ''
        obj_type = elem.is_a()
        
        if global_id in processed_ids:
            continue
        
        # Get floor from structure
        floor_db = floor_key
        if hasattr(elem, 'ContainedInStructure') and elem.ContainedInStructure:
            for rel in elem.ContainedInStructure:
                if rel and hasattr(rel, 'RelatingStructure'):
                    rs = rel.RelatingStructure
                    if rs and hasattr(rs, 'Name') and rs.Name in floor_mapping:
                        floor_db = floor_mapping[rs.Name]
        
        processed_ids.add(global_id)
        
        center_z = 0
        if hasattr(elem, 'ObjectPlacement') and elem.ObjectPlacement:
            try:
                placement = elem.ObjectPlacement
                if hasattr(placement, 'RelativePlacement') and placement.RelativePlacement:
                    rp = placement.RelativePlacement
                    if hasattr(rp, 'PlacementOrigin') and rp.PlacementOrigin:
                        if hasattr(rp.PlacementOrigin, 'Coordinates'):
                            coords = rp.PlacementOrigin.Coordinates
                            if coords and len(coords) > 2:
                                center_z = coords[2]
            except:
                pass
        
        rooms.append({
            'id': global_id,
            'name': name[:50] if name else f'Room_{global_id}',
            'floor': floor_db,
            'type': obj_type,
            'area': round(50, 2),  # estimated area
            'capacity': 30,
            'equipment': '',
            'year_built': None,
            'maintenance_status': 'Good',
            'risk_level': 'Low',
            'temperature': None,
            'noise_db': None,
            'lighting_lux': None,
            'latitude': None,
            'longitude': None,
            'center_x': 0,
            'center_y': 0,
            'center_z': round(center_z, 2)
        })

# Write CSV
output_path = 'src/data/bim/rooms.csv'
with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=[
        'id', 'name', 'floor', 'type', 'area', 'capacity', 'equipment',
        'year_built', 'maintenance_status', 'risk_level',
        'temperature', 'noise_db', 'lighting_lux',
        'latitude', 'longitude', 'center_x', 'center_y', 'center_z'
    ])
    writer.writeheader()
    writer.writerows(rooms)

print(f'\\nRooms CSV written to {output_path}')
print(f'Total rooms: {len(rooms)}')

# Show floor distribution
from collections import Counter
floor_counts = Counter(r['floor'] for r in rooms)
print(f'Floor distribution: {dict(floor_counts)}')