from pprint import pprint

from nexus_ai.adapters.calendar import GoogleCalendarAdapter


def main() -> None:
    adapter = GoogleCalendarAdapter()
    event = adapter.create_demo_event("nexus_ai demo appointment")
    print("CREATED_EVENT")
    pprint(event)


if __name__ == "__main__":
    main()
