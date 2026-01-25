import sys
import os
import runpy
import threading

# Configuration
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), 'sequence_diagram.mmd')
TARGET_MODULES = ['gcsynth', 'src'] # Filter to keep diagram readable

class MermaidTracer:
    def __init__(self):
        self.stack = []
        self.events = []
        self.participants = set()

    def _get_name(self, frame, arg, event):
        if event in ('c_call', 'c_return'):
            # C-Extension function
            func_name = arg.__name__
            module = getattr(arg, '__module__', 'C_Module')
            return module, func_name
        else:
            # Python function
            code = frame.f_code
            func_name = code.co_name
            # Try to get module name from filename
            filename = code.co_filename
            module = 'Unknown'
            
            # Simple heuristic to clean up module names
            if 'src' in filename:
                parts = filename.split(os.sep)
                try:
                    idx = parts.index('src')
                    module = ".".join(parts[idx:])
                    module = module.replace('.py', '')
                except ValueError:
                    module = os.path.basename(filename)
            else:
                module = os.path.basename(filename)
            
            return module, func_name

    def trace(self, frame, event, arg):
        if event not in ('call', 'return', 'c_call', 'c_return'):
            return
        
        module, func_name = self._get_name(frame, arg, event)

        # Filter noise: Only trace relevant modules
        if not any(m in module for m in TARGET_MODULES):
            return

        # Clean up participant names for Mermaid (no dots/slashes)
        participant = module.replace('/', '_').replace('.', '_').replace('\\', '_')
        self.participants.add(participant)

        if event in ('call', 'c_call'):
            caller = self.stack[-1] if self.stack else "Main"
            self.events.append(f"{caller}->>{participant}: {func_name}()")
            self.events.append(f"activate {participant}")
            self.stack.append(participant)
        
        elif event in ('return', 'c_return'):
            if self.stack:
                callee = self.stack.pop()
                # Only record return if it matches (simple stack check)
                if callee == participant:
                    caller = self.stack[-1] if self.stack else "Main"
                    self.events.append(f"{participant}-->>{caller}: return")
                    self.events.append(f"deactivate {participant}")

    def save(self):
        print(f"Saving sequence diagram to {OUTPUT_FILE}...")
        with open(OUTPUT_FILE, 'w') as f:
            f.write("sequenceDiagram\n")
            for p in sorted(self.participants):
                f.write(f"    participant {p}\n")
            for e in self.events:
                f.write(f"    {e}\n")
        print("Done.")

def main():
    if len(sys.argv) < 2:
        print("Usage: python sequence_tracer.py <script_to_run>")
        sys.exit(1)

    target_script = sys.argv[1]
    tracer = MermaidTracer()
    
    # Setup path to include src so imports work
    src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../src'))
    sys.path.insert(0, src_path)

    sys.setprofile(tracer.trace)
    try:
        # Run the target script
        sys.argv = [target_script] # Reset argv for the target
        runpy.run_path(target_script, run_name="__main__")
    except SystemExit:
        pass
    finally:
        sys.setprofile(None)
        tracer.save()

if __name__ == "__main__":
    main()