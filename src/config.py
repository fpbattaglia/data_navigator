import json
import os

project_dir = os.path.join(os.path.dirname(__file__), os.pardir)

with open(os.path.join(project_dir, 'src', 'config.json')) as f:
    project_metadata = json.load(f)



