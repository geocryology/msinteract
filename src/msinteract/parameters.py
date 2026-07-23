import re
import numpy as np
from groundmodel.core.geometry import resample_properties, thickness_to_midpoint


def is_namedtuple_instance(obj):
    return isinstance(obj, tuple) and hasattr(obj, "_fields")


class MeshParameters:
    SOIL_PARAMS = ['sand', 'clay', 'wsoil', 'isoil', 'tpsoil']  # shares layer dimension

    def __init__(self, filepath=None):
        """ Wrapper for MESH_parameters.txt file, which contains soil properties and other parameters for MESH-SVS2. 
        It preserves the original file structure, including comments and blank lines, while allowing programmatic access to parameter values.
        
        Parameters
        ----------
        filepath : str, optional
            Path to an existing MESH_parameters.txt file to read
        """
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

    def nlayers(self):
        """Returns the number of soil layers based on the length of soil parameter arrays."""
        lens = []
        for p in self.SOIL_PARAMS:
            values = self.get(p)
            if isinstance(values, np.ndarray):
                lens.append(len(values))
        
        if not len(set(lens)) <= 1:
            raise ValueError(f"Inconsistent number of layers among soil parameters: {dict(zip(self.SOIL_PARAMS, lens))}")
        
        return lens[0] if lens else 0

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

    def keys(self):
        return [node['key'] for node in self.nodes if node['type'] == 'param']
    
    def params(self):
        return {node['key']: self._parse_value(node['value']) for node in self.nodes if node['type'] == 'param'}
    
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
                if is_namedtuple_instance(new_value):  # pre-convert named tuples to arrays
                    new_value = np.array(new_value) 
                if isinstance(new_value, np.ndarray):
                    # Format floats to avoid excessive decimals if desired
                    node['value'] = " ".join(map(str, new_value.tolist()))
                elif isinstance(new_value, (list, tuple)):
                    node['value'] = " ".join(map(str, new_value))
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

    def rediscretize(self, current_thicknesses, new_thicknesses):
        """Rediscretizes soil parameters to match new layer thicknesses."""

        target_z = thickness_to_midpoint(new_thicknesses)
        target_dz = new_thicknesses
        source_thicknesses = current_thicknesses
        new_params = {}
        for p in self.SOIL_PARAMS:  # Ensure success before modifying any parameters
            source_values = np.atleast_1d(self.get(p))
            if hasattr(source_values, '__len__') and len(source_values) < len(source_thicknesses):  
                # in MESH file, last value applies to all deeper layers
                source_values = np.array(list(source_values) + [source_values[-1]] * (len(source_thicknesses) - len(source_values)))
            
            new_params[p] = resample_properties(target_z=target_z,
                                                target_dz=target_dz,
                                                source_thicknesses=source_thicknesses,
                                                source_values=source_values)

        for p, values in new_params.items():
            self.set(p, values)


def format_value_for_output(val) -> str:
    """Convert a node value into a clean, space-delimited string."""
    # None → empty field
    if val is None:
        return ""
    import pdb;pdb.set_trace()
    # NumPy scalar → convert to float
    if hasattr(val, "item") and not hasattr(val, "__len__"):
        return str(float(val))

    # NumPy array → flatten and convert
    try:
        import numpy as np
        if isinstance(val, np.ndarray):
            return " ".join(str(float(v)) for v in val.ravel())
    except Exception:
        pass

    # List / tuple → space-delimited values
    if isinstance(val, (list, tuple)):
        out = []
        for v in val:
            # NumPy scalar inside list
            if hasattr(v, "item"):
                v = float(v)
            out.append(str(v))
        return " ".join(out)

    # Everything else → string
    return str(val)



if __name__ == "__main__":
    config = MeshParameters('mesh_config.txt')

    sand_values = config.get('sand')
    
    if isinstance(sand_values, np.ndarray):
        new_sand = sand_values + 5.0 
        config.set('sand', new_sand)

    print(f"Latitude: {config.get('deglat')}")

    config.set('lmacropores_svs', True)

    config.write('updated_mesh_config.txt')