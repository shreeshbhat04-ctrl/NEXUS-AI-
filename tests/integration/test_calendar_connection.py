from pprint import pprint

from nexus_ai.adapters.calendar import GoogleCalendarAdapter


def main() -> None:
    adapter = GoogleCalendarAdapter()
    events = adapter.list_upcoming_events()
    print("CALENDAR_EVENTS")
    pprint(events)


if __name__ == "__main__":
    main()
