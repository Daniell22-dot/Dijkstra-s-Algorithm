"""
Generate src/js/config.js from the Cesium ion token in .env.

The generated file is gitignored so the token is never committed.

Usage:
    python generate_frontend_config.py
"""

import json
import os
from dotenv import dotenv_values

ROOT = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(ROOT, '.env')
OUT_PATH = os.path.join(ROOT, 'src', 'js', 'config.js')

KEYS = ('CESIUM_ION_TOKEN', 'CESIUM_TOKEN', 'Token', 'token')


def main():
    values = dotenv_values(ENV_PATH)
    token = next((values.get(key) for key in KEYS if values.get(key)), None)
    if not token:
        raise SystemExit(f'No Cesium ion token found in {ENV_PATH}')

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, 'w', encoding='utf-8') as handle:
        handle.write(f'window.CESIUM_ION_TOKEN = {json.dumps(token)};\n')
    print(f'Wrote {os.path.relpath(OUT_PATH, ROOT)} (token length {len(token)})')


if __name__ == '__main__':
    main()
