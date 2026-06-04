import json

# Simulate what the generation script produces
s = r'r"$4\times10^{-19}$"'
print('Python string value:', repr(s))
print()

json_str = json.dumps(s)
print('JSON output:', json_str)
print()

# Simulate what Jupyter reads
parsed = json.loads(json_str)
print('After JSON parse:', repr(parsed))
print()

# Now simulate the full cell source
source_lines = [
    r'("Hamaker constant $A$", r"$4\times10^{-19}$", "J"),',
]
full_source = ''.join(source_lines)
print('Full source:', repr(full_source))
print()

# Check what JSON looks like for the full notebook cell
nb = {"cells": [{"source": source_lines}]}
json_nb = json.dumps(nb)
print('Notebook JSON snippet:', json_nb[:200])
print()

# Parse back
nb2 = json.loads(json_nb)
parsed_source = ''.join(nb2["cells"][0]["source"])
print('Parsed source:', repr(parsed_source))
