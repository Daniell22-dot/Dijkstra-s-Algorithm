import ifcopenshell
import csv
import os

ds = ifcopenshell.open('D:/deKUT-3D-Campus-Digital-Twin/src/data/bim/DANIEL.ifc')

# Export Windows to CSV
windows = list(ds.by_type('IfcWindow'))
print(f'Exporting {len(windows)} windows...')

window_data = []
for window in windows:
    # Get basic attributes
    global_id = window.GlobalId if hasattr(window, 'GlobalId') else ''
    name = window.Name if hasattr(window, 'Name') else ''
    obj_type = window.ObjectType if hasattr(window, 'ObjectType') else ''
    
    # Get PredefinedType
    predefined_type = ''
    if hasattr(window, 'PredefinedType') and window.PredefinedType:
        predefined_type = window.PredefinedType.name if hasattr(window.PredefinedType, 'name') else str(window.PredefinedType)
    
    # Get floor from ContainedInStructure
    floor = ''
    if hasattr(window, 'ContainedInStructure') and window.ContainedInStructure:
        for rel in window.ContainedInStructure:
            if rel:
                related_entity = rel.RelatingStructure
                if related_entity:
                    floor = related_entity.Name if hasattr(related_entity, 'Name') else str(related_entity)
    
    # Get width/height from WindowType
    width = ''
    height = ''
    if window.IsTypedBy and window.IsTypedBy[0]:
        type_obj = window.IsTypedBy[0].RelatingType
        if type_obj and hasattr(type_obj, 'OverallWidth'):
            width = str(type_obj.OverallWidth) if type_obj.OverallWidth else ''
        if type_obj and hasattr(type_obj, 'OverallHeight'):
            height = str(type_obj.OverallHeight) if type_obj.OverallHeight else ''
    
    # Material
    material = ''
    if hasattr(window, 'HasAssociations') and window.HasAssociations:
        for assoc in window.HasAssociations:
            if assoc:
                for rel in assoc:
                    if hasattr(rel, 'Name'):
                        material = rel.Name
    
    window_data.append({
        'id': global_id,
        'name': name,
        'floor': floor,
        'width': width,
        'height': height,
        'material': material,
        'status': 'Good'
    })

# Write CSV
output_path = 'src/data/bim/windows.csv'
with open(output_path, 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['id', 'name', 'floor', 'width', 'height', 'material', 'status'])
    writer.writeheader()
    writer.writerows(window_data)

print(f'Windows CSV written to {output_path}')
print(f'Total windows: {len(window_data)}')
print(f'First window: {window_data[0] if window_data else "none"}')