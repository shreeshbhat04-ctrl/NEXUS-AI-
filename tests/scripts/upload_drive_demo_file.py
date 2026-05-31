from pathlib import Path
from pprint import pprint

from nexus_ai.adapters.drive import GoogleDriveAdapter


def main() -> None:
    sample_path = Path("docs/CONNECTION_ARCHITECTURE.md")
    adapter = GoogleDriveAdapter()
    result = adapter.upload_file(str(sample_path), mime_type="text/markdown")
    print("UPLOADED_FILE")
    pprint(result)


if __name__ == "__main__":
    main()
