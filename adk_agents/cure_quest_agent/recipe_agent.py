from pathlib import Path
import sys

repo_root = Path(__file__).resolve().parents[2]
src_path = repo_root / "src"

if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from nexus_ai.adk.recipe_agent import recipe_agent as root_agent
