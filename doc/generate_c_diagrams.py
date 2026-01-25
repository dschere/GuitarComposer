import os
import re
import sys

# Paths
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
SRC_DIR = os.path.join(PROJECT_ROOT, 'src', 'cmodules', 'gcsynth')
OUT_DIR = os.path.join(PROJECT_ROOT, 'doc', 'mermaid')

def ensure_dir(d):
    if not os.path.exists(d):
        os.makedirs(d)

def get_function_map(src_dir):
    """
    Scans all .c files to map function names to their defining module (filename).
    """
    func_map = {}
    modules = {}
    
    # Regex for C function definition (simplified)
    # Matches: Type name(
    # Excludes: if(, while(, etc.
    def_pattern = re.compile(r'^\s*(?:\w+\s+)+(\w+)\s*\(', re.MULTILINE)
    
    for root, _, files in os.walk(src_dir):
        for filename in files:
            if filename.endswith('.c'):
                module_name = os.path.splitext(filename)[0]
                filepath = os.path.join(root, filename)
                modules[module_name] = filepath
                
                with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Remove comments for parsing
                    content = re.sub(r'//.*', '', content)
                    content = re.sub(r'/\*.*?\*/', '', content, flags=re.DOTALL)
                    
                    matches = def_pattern.findall(content)
                    for func_name in matches:
                        if func_name not in ['if', 'while', 'for', 'switch', 'sizeof']:
                            func_map[func_name] = module_name
                            
    return func_map, modules

def generate_diagrams(func_map, modules):
    """
    Parses each module again to find calls to external functions and generates Mermaid files.
    """
    
    # Regex for function calls
    call_pattern = re.compile(r'(\w+)\s*\(')
    # Regex to detect which function we are currently inside
    func_start_pattern = re.compile(r'^\s*(?:\w+\s+)+(\w+)\s*\(')

    for module_name, filepath in modules.items():
        print(f"Generating diagram for {module_name}...")
        
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = f.readlines()
            
        interactions = [] # List of (caller_func, target_module, target_func)
        current_func = "Global/Setup"
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('//') or line.startswith('/*'):
                continue
                
            # Check if entering a new function definition
            m_def = func_start_pattern.match(line)
            if m_def:
                fname = m_def.group(1)
                if fname not in ['if', 'while', 'for', 'switch']:
                    current_func = fname
            
            # Check for function calls
            calls = call_pattern.findall(line)
            for called_func in calls:
                if called_func in func_map:
                    target_module = func_map[called_func]
                    
                    # Only record cross-module calls for clarity
                    if target_module != module_name:
                        interactions.append((current_func, target_module, called_func))

        if not interactions:
            continue

        # Generate Mermaid Content
        mmd_path = os.path.join(OUT_DIR, f"{module_name}.mmd")
        with open(mmd_path, 'w') as f:
            f.write("sequenceDiagram\n")
            f.write(f"    participant {module_name}\n")
            
            # Collect other participants
            others = sorted(list(set(t for _, t, _ in interactions)))
            for o in others:
                f.write(f"    participant {o}\n")
            
            f.write("\n")
            
            # Write interactions
            for caller, target, func in interactions:
                f.write(f"    {module_name}->>{target}: {func}()\n")
                f.write(f"    Note right of {module_name}: inside {caller}\n")

def main():
    ensure_dir(OUT_DIR)
    print(f"Scanning {SRC_DIR}...")
    func_map, modules = get_function_map(SRC_DIR)
    print(f"Found {len(func_map)} functions in {len(modules)} modules.")
    generate_diagrams(func_map, modules)
    print(f"Mermaid files written to {OUT_DIR}")

if __name__ == "__main__":
    main()