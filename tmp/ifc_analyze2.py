import ifcopenshell

ds = ifcopenshell.open('D:/deKUT-3D-Campus-Digital-Twin/src/data/bim/DANIEL.ifc')
elements = list(ds.by_type('IfcBuildingElement'))[:3]  # First 3 elements

# Check all attributes for each element
for elem in elements:
    print(f'\nElement: {elem.GlobalId} - {elem.Name}')
    print(f'  IsA: {elem.is_a()}')
    # Get all attributes/methods
    attrs = [a for a in dir(elem) if not a.startswith('_')]
    print(f'  Attributes: {attrs}')
    # Try to get COORDINATES or Position
    try:
        if hasattr(elem, 'Representation') and elem.Representation:
            reprs = elem.Representation.items if hasattr(elem.Representation, 'items') else [elem.Representation]
            for item in (reprs if isinstance(reprs, list) else [reprs]):
                if hasattr(item, 'Points'):
                    print(f'  Points count: {len(item.Points)}')
                    if item.Points:
                        print(f'  First point: {item.Points[0]}')
    except Exception as e:
        print(f'  Error: {e}')
PYEOF