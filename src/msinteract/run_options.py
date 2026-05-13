import re
import os

def read_run_option_flag(file_path, key):
    """
    Searches for a key and returns its value.
    Example: 'SHDFILEFLAG' -> '2'
    """
    # Pattern: Line start, optional whitespace, the key, 
    # then capture everything until a comment (#) or end of line.
    pattern = rf"^\s*{re.escape(key)}\s+([^#\n\r]+)"
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    return match.group(1).strip()
    except FileNotFoundError:
        return None
    return None


def set_run_option_flag(file_path, key, value):
    """
    Updates an existing key with a new value while preserving 
    the trailing comments and structure.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Target file {file_path} not found.")

    # Pattern: (Key + space) (Value) (Optional comment/space)
    # Group 1: Key and leading space
    # Group 2: The old value (to be replaced)
    # Group 3: Everything after the value (comments, etc)
    pattern = rf"(^\s*{re.escape(key)}\s+)([^#\n\r]+)(.*)"
    
    lines = []
    found = False
    
    with open(file_path, 'r') as f:
        for line in f:
            match = re.search(pattern, line, re.IGNORECASE)
            if match:
                # Reconstruct line: Key + New Value + Old Comments
                new_line = f"{match.group(1)}{value}\t{match.group(3).strip()}\n"
                lines.append(new_line)
                found = True
            else:
                lines.append(line)
    
    if found:
        with open(file_path, 'w') as f:
            f.writelines(lines)
        print(f"Updated '{key}' to '{value}' in {file_path}")
    
    return found