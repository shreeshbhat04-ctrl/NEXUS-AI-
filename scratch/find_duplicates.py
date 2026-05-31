import re
import argparse
import os
from collections import Counter
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET = REPO_ROOT / "src" / "nexus_ai" / "api" / "models.py"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Find duplicate BaseModel class names in a Python file.")
    parser.add_argument(
        "--file",
        default=os.environ.get("FIND_DUPLICATES_TARGET", str(DEFAULT_TARGET)),
        help="Python file to scan. Defaults to src/nexus_ai/api/models.py or FIND_DUPLICATES_TARGET.",
    )
    return parser.parse_args()


args = parse_args()
file_path = Path(args.file).expanduser()
if not file_path.is_absolute():
    file_path = REPO_ROOT / file_path

content = file_path.read_text(encoding="utf-8")

classes = re.findall(r'^class (\w+)\(BaseModel\):', content, re.MULTILINE)
duplicates = [name for name, count in Counter(classes).items() if count > 1]

if duplicates:
    print(f"Found duplicate classes: {duplicates}")
else:
    print("No duplicate classes found.")
