"""Generate Python gRPC stubs from .proto files.

Usage:
    python scripts/generate_protos.py

This script compiles all .proto files in src/nexus_ai/proto/ and outputs
the generated _pb2.py and _pb2_grpc.py files into src/nexus_ai/generated/.
"""
import subprocess
import sys
from pathlib import Path


def main() -> None:
    project_root = Path(__file__).resolve().parent.parent
    proto_dir = project_root / "src" / "nexus_ai" / "proto"
    output_dir = project_root / "src" / "nexus_ai" / "generated"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Ensure __init__.py exists in generated/
    init_file = output_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text('"""Auto-generated gRPC stubs. Do not edit manually."""\n')

    proto_files = list(proto_dir.glob("*.proto"))
    if not proto_files:
        print("No .proto files found in", proto_dir)
        sys.exit(1)

    print(f"Found {len(proto_files)} proto files: {[p.name for p in proto_files]}")
    print(f"Output directory: {output_dir}")

    cmd = [
        sys.executable, "-m", "grpc_tools.protoc",
        f"--proto_path={proto_dir}",
        f"--python_out={output_dir}",
        f"--grpc_python_out={output_dir}",
    ] + [str(p) for p in proto_files]

    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.returncode != 0:
        print("ERROR: protoc failed!")
        print(result.stderr)
        sys.exit(result.returncode)

    # Fix imports in generated files — grpc_tools generates absolute imports
    # that don't work with package structure. Patch them to relative imports.
    generated_files = list(output_dir.glob("*_pb2_grpc.py"))
    for grpc_file in generated_files:
        content = grpc_file.read_text()
        # Replace "import X_pb2" with "from . import X_pb2" for local proto imports
        for proto_file in proto_files:
            module_name = proto_file.stem + "_pb2"
            old_import = f"import {module_name}"
            new_import = f"from . import {module_name}"
            if old_import in content and new_import not in content:
                content = content.replace(old_import, new_import)
        grpc_file.write_text(content)

    print("Successfully generated gRPC stubs:")
    for f in sorted(output_dir.glob("*_pb2*.py")):
        print(f"  {f.name}")


if __name__ == "__main__":
    main()
