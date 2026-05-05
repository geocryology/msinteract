import re
import numpy as np


class MeshParameters:
    def __init__(self, filepath=None):
        self.nodes = []
        if filepath:
            self.read(filepath)

    def read(self, filepath):
        self.nodes = []
        with open(filepath, 'r') as f:
            for line in f:
                stripped = line.strip()
                if not stripped:
                    self.nodes.append({'type': 'blank', 'raw': line})
                    continue
                if stripped.startswith('!'):
                    self.nodes.append({'type': 'comment', 'raw': line})
                    continue

                # Regex: Key, Value(s), and optional Comment
                match = re.match(r'^(\S+)\s+([^!]+)(.*)$', line)
                if match:
                    key = match.group(1)
                    val_str = match.group(2).strip()
                    comment = match.group(3)
                    self.nodes.append({
                        'type': 'param',
                        'key': key,
                        'value': val_str,
                        'comment': comment
                    })
                else:
                    self.nodes.append({'type': 'comment', 'raw': line})

    def _parse_value(self, val_str):
        """Converts raw string values to Python/NumPy types."""
        parts = val_str.split()
        
        # Convert Fortran booleans
        if len(parts) == 1:
            low = parts[0].lower()
            if low == '.true.': return True
            if low == '.false.': return False
            
            # Try to return as float if single value
            try:
                return float(parts[0])
            except ValueError:
                return parts[0]
        
        # Return as NumPy array for multiple values
        try:
            return np.array([float(x) for x in parts])
        except ValueError:
            return np.array(parts)

    def get(self, key):
        """Returns the value as a single item or NumPy array."""
        for node in self.nodes:
            if node.get('type') == 'param' and node.get('key') == key:
                return self._parse_value(node['value'])
        return None

    def set(self, key, new_value):
        """Sets a value, converting NumPy arrays back to space-separated strings."""
        for node in self.nodes:
            if node.get('type') == 'param' and node.get('key') == key:
                if isinstance(new_value, np.ndarray):
                    # Format floats to avoid excessive decimals if desired
                    node['value'] = " ".join(map(str, new_value.tolist()))
                elif isinstance(new_value, bool):
                    node['value'] = '.true.' if new_value else '.false.'
                else:
                    node['value'] = str(new_value)
                return True
        return False

    def write(self, output_path):
        with open(output_path, 'w') as f:
            for node in self.nodes:
                if node['type'] in ['blank', 'comment']:
                    f.write(node['raw'])
                elif node['type'] == 'param':
                    # align keys at 18 chars for readability
                    line = f"{node['key'].ljust(18)} {node['value']}{node['comment']}\n"
                    f.write(line)


if __name__ == "__main__":
    # Assuming the file provided in your prompt is 'mesh_config.txt'
    config = MeshParameters('mesh_config.txt')

    # Get multi-value row (sand)
    sand_values = config.get('sand')
    print(f"Sand (type {type(sand_values)}): {sand_values}")
    
    # Perform math with NumPy
    if isinstance(sand_values, np.ndarray):
        new_sand = sand_values + 5.0 
        config.set('sand', new_sand)

    # Get single value
    print(f"Latitude: {config.get('deglat')}")

    # Set boolean using Python True/False
    config.set('lmacropores_svs', True)

    config.write('updated_mesh_config.txt')