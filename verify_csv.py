import csv
import os

bim_dir = 'src/data/bim'
files = ['rooms.csv', 'doors.csv', 'windows.csv']

for f in files:
    path = os.path.join(bim_dir, f)
    print(f'\n=== {f} ===')
    with open(path, 'r', encoding='utf-8') as fh:
        reader = csv.DictReader(fh)
        rows = list(reader)
        print(f'Total rows: {len(rows)}')
        print(f'Headers: {list(rows[0].keys()) if rows else "empty"}')
        if rows:
            first = rows[0]
            # Print first 5 keys
            keys_list = list(first.keys())
            print(f'First 5 keys: {keys_list[:5]}')
            print(f'First row sample: { {k: first[k] for k in keys_list[:5]} }')