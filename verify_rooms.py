import csv

with open('src/data/bim/rooms.csv', 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    rows = list(reader)
    print(f'Total: {len(rows)}')
    # Show floor distribution
    floors = {}
    for r in rows:
        floor = r['floor']
        floors[floor] = floors.get(floor, 0) + 1
    print(f'Floors: {floors}')
    # Show first few rows
    for r in rows[:3]:
        print(f'  ID: {r["id"]} | Name: {r["name"]} | Floor: {r["floor"]} | Type: {r["type"]}')