import ifcopenshell
import csv
import os

ds = ifcopenshell.open('D:/deKUT-3D-Campus-Digital-Twin/src/data/bim/DANIEL.ifc')

# Try to find IfcSpace or similar spatial elements
# If not available, create rooms from building elements with spatial data

# First, check for any spatial structure
all_types = set()
for elem in list(ds.by_type('IfcBuildingElement')):
    t = elem.is_a()
    all_types.add(t)

# Look for spatial containers
print('Available entity types:')
for t in sorted(all_types):
    if any(x in t for x in ['Space', 'Room', 'Building', 'Story', 'Foot', 'Placement', 'Map']):
        print(f'  {t}')

# Get columns and beams which have spatial positions
columns = list(ds.by_type('IfcColumn'))[:20]
beams = list(ds.by_type('IfcBeam'))[:20]

print(f'\\nSample columns (first 3):')
for c in columns[:3]:
    gid = c.GlobalId if hasattr(c, 'GlobalId') else ''
    name = c.Name if hasattr(c, 'Name') else ''
    obj_type = c.ObjectType if hasattr(c, 'ObjectType') else ''
    print(f'  GlobalId: {gid}, Name: {name}, ObjectType: {obj_type}')

print(f'\\nSample beams (first 3):')
for b in beams[:3]:
    gid = b.GlobalId if hasattr(b, 'GlobalId') else ''
    name = b.Name if hasattr(b, 'Name') else ''
    obj_type = b.ObjectType if hasattr(b, 'ObjectType') else ''
    print(f'  GlobalId: {gid}, Name: {name}, ObjectType: {obj_type}')

# Try to get ObjectPlacement for position data
print(f'\\nChecking ObjectPlacement for columns:')
for c in columns[:3]:
    placement = c.ObjectPlacement
    if placement:
        print(f'  {c.GlobalId}: {placement.is_a()}')
        # Try to get coordinates from placement
        try:
            if placement.is_a() == 'IfcLocalPlacement':
                # Get the mapped items
                for item in placement.RelativeTo[0].Items if hasattr(placement.RelativeTo, '0') else []:
                    if hasattr(item, 'Coordinates'):
                        print(f'    Coordinates: {item.Coordinates}')
        except Exception as e:
            print(f'  Error: {e}')