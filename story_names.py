import ifcopenshell
ds = ifcopenshell.open('D:/deKUT-3D-Campus-Digital-Twin/src/data/bim/DANIEL.ifc')
all_elements = list(ds.by_type('IfcBuildingElement'))

# Check exact story names including any suffixes
story_names = set()
for elem in all_elements:
    if hasattr(elem, 'ContainedInStructure') and elem.ContainedInStructure:
        for rel in elem.ContainedInStructure:
            if rel and hasattr(rel, 'RelatingStructure'):
                rs = rel.RelatingStructure
                if rs and hasattr(rs, 'Name'):
                    story_names.add(rs.Name)

print('Exact story level names:')
for s in sorted(story_names, key=lambda x: x.lower()):
    print(f'  "{s}"')