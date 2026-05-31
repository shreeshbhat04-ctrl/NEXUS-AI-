import subprocess
import sys
import time
import os

env = os.environ.copy()
# Add 'src' to PYTHONPATH so it can find 'nexus_ai'
src_path = os.path.join(os.getcwd(), "src")
if "PYTHONPATH" in env:
    env["PYTHONPATH"] = f"{src_path}{os.pathsep}{env['PYTHONPATH']}"
else:
    env["PYTHONPATH"] = src_path

# Use sys.executable to ensure we use the virtual environment's python
python_exe = sys.executable

services = [
    ("Brain Server", [python_exe, "-m", "nexus_ai.grpc_services.brain_server"]),
    ("Integration Server", [python_exe, "-m", "nexus_ai.grpc_services.integration_server"]),
    ("Clinical Server", [python_exe, "-m", "nexus_ai.grpc_services.clinical_server"]),
    ("Vision Server", [python_exe, "-m", "nexus_ai.grpc_services.vision_server"]),
    ("Diet Server", [python_exe, "-m", "nexus_ai.grpc_services.diet_server"]),
    ("Doctor Server", [python_exe, "-m", "nexus_ai.grpc_services.doctor_server"]),
]

processes = []

try:
    print("Starting gRPC Microservices...")
    for name, cmd in services:
        print(f"Starting {name}...")
        p = subprocess.Popen(cmd, env=env)
        processes.append((name, p))
        time.sleep(1)  # Stagger startup

    print("\nAll gRPC services started.")
    print("Starting FastAPI Gateway...\n")
    
    fastapi_cmd = [sys.executable, "-m", "uvicorn", "nexus_ai.app:app", "--reload"]
    fastapi_process = subprocess.Popen(fastapi_cmd, env=env)
    processes.append(("FastAPI Gateway", fastapi_process))
    
    fastapi_process.wait()

except KeyboardInterrupt:
    print("\nShutting down all services...")
finally:
    for name, p in processes:
        if p.poll() is None:
            print(f"Terminating {name}...")
            p.terminate()
            p.wait()
    print("All services stopped.")
