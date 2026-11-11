import ifcopenshell
import csv
import os

ds = ifcopenshell.open('D:/deKUT-3D-Campus-Digital-Twin/src/data/bim/DANIEL.ifc')

# Extract IfcRailing elements (corridors/railings)
railings = list(ds.by_type('IfcRailing'))
print(f'IfcRailing elements: {len(railings)}')

# Extract IfcStair elements (staircases)
stairs = list(ds.by_type('IfcStair'))
print(f'IfcStair elements: {len(stairs)}')

# Get all building elements to analyze connections
all_elements = list(ds.by_type('IfcBuildingElement'))

# Analyze type breakdown
type_counts = {}
for elem in all_elements:
    t = elem.is_a()
    type_counts[t] = type_counts.get(t, 0) + 1

print(f'\\nElement type breakdown:')
for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
    print(f'  {t}: {c}')

# Get unique GlobalIds for doors, windows, stairs
door_ids = [e.GlobalId for e in all_elements if e.is_a() == 'IfcDoor']
window_ids = [e.GlobalId for e in all_elements if e.is_a() == 'IfcWindow']
stair_ids = [e.GlobalId for e in all_elements if e.is_a() == 'IfcStair']

print(f'\\nDoors: {len(door_ids)}')
print(f'Windows: {len(window_ids)}')
print(f'Stairs: {len(stair_ids)}')

# Extract corridor network from element connections
# Look at HasAssociations and ContainedInStructure to understand spatial layout
print('\\n=== Spatial Analysis ===')

# Check if elements are contained in spatial structures
spatial_elements = []
for elem in all_elements[:50]:  # Sample
    if hasattr(elem, 'ContainedInStructure') and elem.ContainedInStructure:
        for rel in elem.ContainedInStructure:
            if rel and hasattr(rel, 'RelatingStructure'):
                rs = rel.RelatingStructure
                if rs and hasattr(rs, 'Name'):
                    spatial_elements.append({
                        'global_id': elem.GlobalId if hasattr(elem, 'GlobalId') else '',
                        'name': elem.Name if hasattr(elem, 'Name') else '',
                        'type': elem.is_a(),
                        'relating_structure': rs.Name
                    })

print(f'Sample elements with spatial containment: {len(spatial_elements)}')
for se in spatial_elements[:10]:
    print(f'  {se["type"]}: {se["name"][:30] if se["name"] else ""} | Contained in: {se["relating_structure"]}')

# Check ObjectPlacement for positions
print('\\n=== Position Analysis ===')
position_count = 0
zero_z_count = 0
for elem in all_elements[:100]:
    if hasattr(elem, 'ObjectPlacement') and elem.ObjectPlacement:
        position_count += 1
        try:
            placement = elem.ObjectPlacement
            z = 0
            if hasattr(placement, 'RelativePlacement') and placement.RelativePlacement:
                rp = placement.RelativePlacement
                if hasattr(rp, 'PlacementOrigin') and rp.PlacementOrigin:
                    if hasattr(rp.PlacementOrigin, 'Coordinates'):
                        coords = rp.PlacementOrigin.Coordinates
                        if coords and len(coords) > 2:
                            z = coords[2]
            if z == 0:
                zero_z_count += 1
            elif z != 0:
                # First non-zero Z we see
                if zero_z_count == 100:  # only print first few non-zero
                    print(f'{elem.GlobalId}: Z={z}')
        except:
            pass

print(f'\\nElements with ObjectPlacement in sample: {position_count}')
print(f'Elements with Z=0 in sample: {zero_z_count}')