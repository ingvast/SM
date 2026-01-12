import yaml
import sys
import argparse

from codegen.common import generate_dot
from codegen.c_lang import CGenerator
# from codegen.rust_lang import RustGenerator

def main():
    parser = argparse.ArgumentParser(description="State Machine Generator")
    parser.add_argument("file", help="Input YAML file")
    parser.add_argument("--lang", choices=['c', 'rust'], default='c', help="Output language")
    args = parser.parse_args()

    with open(args.file, 'r') as f:
        data = yaml.safe_load(f)

    # 1. Generate DOT (Always)
    dot_content = generate_dot(data)
    with open("statemachine.dot", "w") as f:
        f.write(dot_content)
    print("Generated statemachine.dot")

    # 2. Generate Code
    if args.lang == 'c':
        gen = CGenerator(data)
        header, source = gen.generate()
        with open("statemachine.h", "w") as f: f.write(header)
        with open("statemachine.c", "w") as f: f.write(source)
        print("Generated statemachine.c/.h")
        
    elif args.lang == 'rust':
        print("Rust generation coming soon!")
        from codegen.rust_lang import RustGenerator
        gen = RustGenerator(data)
        source, _ = gen.generate()
        with open("statemachine.rs", "w") as f: f.write(source)
        print("Generated statemachine.rs")

if __name__ == "__main__":
    main()
