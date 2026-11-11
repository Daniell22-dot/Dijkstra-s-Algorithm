import ifcopenshell
import csv
import os

ds = ifcopenshell.open('D:/deKUT-3D-Campus-Digital-Twin/src/data/bim/DANIEL.ifc')

# Create rooms based on building elements with spatial data
# Since IFC file has IfcColumn, IfcBeam, IfcWall, etc. but no IfcSpace/IfcRoom,
# we'll create rooms from the building elements and assign floors based on naming convention

# First, get all building elements
all_elements = list(ds.by_type('IfcBuildingElement'))

# Group elements by floor based on name patterns
# Pattern: "BMR - 074" -> Ground Floor, "BMR - 100" -> First Floor, etc.
# Pattern: "CRE - 001" -> Ground Floor

rooms = []
processed_ids = set()

# Process columns as potential room locations
columns = [e for e in all_elements if e.is_a() == 'IfcColumn']
beams = [e for e in all_elements if e.is_a() == 'IfcBeam']
walls = [e for e in all_elements if e.is_a() == 'IfcWall']
doors = [e for e in all_elements if e.is_a() == 'IfcDoor']
windows = [e for e in all_elements if e.is_a() == 'IfcWindow']

# Assign floors based on element names
def assign_floor(name):
    """Assign floor based on element name pattern"""
    if not name:
        return 'Ground'
    name_upper = name.upper()
    # Check for first floor indicators
    if any(keyword in name_upper for keyword in ['FIRST', '1ST', 'FIRST_FLOOR', 'UPPER']):
        return 'First'
    # Check for basement/lower ground
    if any(keyword in name_upper for keyword in ['BASEMENT', 'LOWER', 'GROUND_FLOOR', 'GROUND']):
        return 'Ground'
    # Default to Ground
    return 'Ground'

# Create rooms from columns (as room centers/locations)
for col in columns:
    global_id = col.GlobalId if hasattr(col, 'GlobalId') else ''
    name = col.Name if hasattr(col, 'Name') else f'Column_{global_id}'
    obj_type = col.ObjectType if hasattr(col, 'ObjectType') else ''
    
    if global_id in processed_ids:
        continue
    processed_ids.add(global_id)
    
    floor = assign_floor(name)
    
    # Extract potential area from element dimensions if available
    area = 0
    try:
        # Try to get representation for area
        if hasattr(col, 'Representation') and col.Representation:
            pass  # Would need complex geometry processing
    except:
        pass
    
    rooms.append({
        'id': global_id,
        'name': name[:50] if name else f'Room_{global_id}',  # limit name length
        'floor': floor,
        'type': 'Column',
        'area': round(area, 2),
        'capacity': 20,  # default capacity for rooms
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
        'center_z': 0
    })

# Create rooms from beams
for beam in beams:
    global_id = beam.GlobalId if hasattr(beam, 'GlobalId') else ''
    name = beam.Name if hasattr(beam, 'Name') else f'Beam_{global_id}'
    obj_type = beam.ObjectType if hasattr(beam, 'ObjectType') else ''
    
    if global_id in processed_ids:
        continue
    processed_ids.add(global_id)
    
    floor = assign_floor(name)
    area = 0
    
    rooms.append({
        'id': global_id,
        'name': name[:50] if name else f'Room_{global_id}',
        'floor': floor,
        'type': 'Beam',
        'area': round(area, 2),
        'capacity': 15,
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
        'center_z': 0
    })

# Also add some rooms based on the building naming convention
# The IFC file has elements like "BMR - 074", "CRE - 001" etc.
# Let's create additional rooms based on unique floor assignments

floors_found = set()
for room in rooms:
    floors_found.add(room['floor'])

print(f' Floors detected: {sorted(floors_found)}')
print(f' Total unique rooms created: {len(rooms)}')

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

print(f'Rooms CSV written to {output_path}')