import ifcopenshell

ds = ifcopenshell.open('D:/deKUT-3D-Campus-Digital-Twin/src/data/bim/DANIEL.ifc')
elements = list(ds.by_type('IfcBuildingElement'))[:5]  # First 5 elements

# Check properties for each element
for elem in elements:
    print(f'\nElement: {elem.GlobalId if hasattr(elem, "GlobalId") else "N/A"} - {elem.Name if hasattr(elem, "Name") else "N/A"}')
    print(f'  IsA: {elem.is_a()}')
    # Get properties
    if hasattr(elem, 'ObjectType'):
        print(f'  ObjectType: {elem.ObjectType}')
    # Get geometry info
    try:
        representation = elem.Representation
        if representation:
            print(f'  Has Representation')
    except:
        pass
    # Get coordinates if available
    try:
        if hasattr(elem, 'Position') and elem.Position:
            pos = elem.Position
            if hasattr(pos, 'Coordinates'):
                print(f'  Position: {pos.Coordinates}')
    except:
        pass