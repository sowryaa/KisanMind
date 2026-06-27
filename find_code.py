import os
import re
import time

pattern = re.compile(r'\b[A-Z0-9]{4}-[A-Z0-9]{4}\b')

paths_to_search = [
    os.path.expanduser('~/Library/Logs'),
    os.path.expanduser('~/Library/Application Support/Antigravity IDE'),
]

now = time.time()

for base_path in paths_to_search:
    for root, dirs, files in os.walk(base_path):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                # only check files modified in last 30 minutes
                if now - os.path.getmtime(file_path) < 1800:
                    with open(file_path, 'r', errors='ignore') as f:
                        content = f.read()
                        matches = pattern.findall(content)
                        if matches:
                            print(f"Found in {file_path}: {matches}")
            except Exception:
                pass
