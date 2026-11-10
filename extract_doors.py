import ifcopenshell
import csv
import os

ds = ifcopenshell.open('D:/deKUT-3D-Campus-Digital-Twin/src/data/bim/DANIEL.ifc')

# Export Doors to CSV
doors = list(ds.by_type('IfcDoor'))
print(f'Exporting {len(doors)} doors...')

door_data = []
for door in doors:
    # Get basic attributes
    global_id = door.GlobalId if hasattr(door, 'GlobalId') else ''
    name = door.Name if hasattr(door, 'Name') else ''
    obj_type = door.ObjectType if hasattr(door, 'ObjectType') else ''
    
    # Get PredefinedType
    predefined_type = ''
    if hasattr(door, 'PredefinedType') and door.PredefinedType:
        predefined_type = door.PredefinedType.name if hasattr(door.PredefinedType, 'name') else str(door.PredefinedType)
    
    # Get floor from ContainedInStructure
    floor = ''
    if hasattr(door, 'ContainedInStructure') and door.ContainedInStructure:
        for rel in door.ContainedInStructure:
            if rel:
                related_entity = rel.RelatingStructure
                if related_entity:
                    floor = related_entity.Name if hasattr(related_entity, 'Name') else str(related_entity)
    
    # Get width/height from DoorType
    width = ''
    height = ''
    if door.IsTypedBy and door.IsTypedBy[0]:
        type_obj = door.IsTypedBy[0].RelatingType
        if type_obj and hasattr(type_obj, 'OverallWidth'):
            width = str(type_obj.OverallWidth) if type_obj.OverallWidth else ''
        if type_obj and hasattr(type_obj, 'OverallHeight'):
            height = str(type_obj.OverallHeight) if type_obj.OverallHeight else ''
    
    # Material
    material = ''
    if hasattr(door, 'HasAssociations') and door.HasAssociations:
        for assoc in door.HasAssociations:
            if assoc:
                for rel in assoc:
                    if hasattr(rel, 'Name'):
                        material = rel.Name
    
    door_data.append({
        'id': global_id,
        'name': name,
        'floor': floor,
        'width': width,
        'height': height,
        'material': material,
        'status': 'Good'
    })

# Write CSV
output_path = 'src/data/bim/doors.csv'
with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['id', 'name', 'floor', 'width', 'height', 'material', 'status'])
    writer.writeheader()
    writer.writerows(door_data)

print(f'Doors CSV written to {output_path}')
print(f'Total doors: {len(door_data)}')
print(f'First door: {door_data[0] if door_data else "none"}')