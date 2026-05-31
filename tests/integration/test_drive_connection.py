from pprint import pprint

from nexus_ai.adapters.drive import GoogleDriveAdapter


def main() -> None:
    adapter = GoogleDriveAdapter()
    files = adapter.list_accessible_files()
    print("DRIVE_FILES")
    pprint(files)


if __name__ == "__main__":
    main()
