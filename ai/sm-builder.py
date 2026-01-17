import yaml
import sys
import argparse
import os

# Ensure we can import from local directory
sys.path.append(os.getcwd())

from codegen.common import generate_dot
from codegen.c_lang import CGenerator
from codegen.rust_lang import RustGenerator

def main():
    parser = argparse.ArgumentParser(description="State Machine Builder")
    parser.add_argument("file", help="Input YAML file")
    parser.add_argument("--lang", choices=['c', 'rust'], default='c', help="Output language (c or rust)")
    args = parser.parse_args()

    if not os.path.exists(args.file):
        sys.exit(f"Error: File '{args.file}' not found.")

    with open(args.file, 'r') as f:
        data = yaml.safe_load(f)

    # Extract decisions logic
    decisions = data.get('decisions', {})

    # 1. Generate Visuals (DOT)
    print(f"Generating Graphviz DOT...")
    dot_content = generate_dot(data, decisions)
    with open("statemachine.dot", "w") as f:
        f.write(dot_content)
    print(" -> statemachine.dot created.")

    # 2. Generate Code
    if args.lang == 'c':
        print("Generating C code...")
        gen = CGenerator(data)
        header, source = gen.generate()
        with open("statemachine.h", "w") as f: f.write(header)
        with open("statemachine.c", "w") as f: f.write(source)
        print(" -> statemachine.c / .h created.")
        
    elif args.lang == 'rust':
        print("Generating Rust code...")
        gen = RustGenerator(data)
        source, _ = gen.generate()
        with open("statemachine.rs", "w") as f: f.write(source)
        print(" -> statemachine.rs created.")

if __name__ == "__main__":
    main()
