import httpx

from nexus_ai.adapters.ticketing import AsanaTicketingAdapter


class FailingClient:
    def __init__(self, *args, **kwargs) -> None:
        _ = args, kwargs

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def get(self, *args, **kwargs):
        _ = args, kwargs
        raise httpx.ConnectError("Asana unavailable")

    def post(self, *args, **kwargs):
        _ = args, kwargs
        raise httpx.ConnectError("Asana unavailable")


def test_asana_list_tasks_falls_back_to_mock(monkeypatch) -> None:
    monkeypatch.setattr("nexus_ai.adapters.ticketing.httpx.Client", FailingClient)

    adapter = AsanaTicketingAdapter()
    adapter.settings.asana_access_token = "token"
    adapter.settings.asana_project_gid = "project"

    tasks = adapter.list_routine_tasks()

    assert len(tasks) >= 1
    assert tasks[0].task_id.startswith("mock-")


def test_asana_create_ticket_falls_back_to_mock(monkeypatch) -> None:
    monkeypatch.setattr("nexus_ai.adapters.ticketing.httpx.Client", FailingClient)

    adapter = AsanaTicketingAdapter()
    adapter.settings.asana_access_token = "token"
    adapter.settings.asana_project_gid = "project"

    ticket = adapter.create_review_ticket(patient_id=2, summary="Needs review", case_type="doctor_review")

    assert ticket.ticket_id.startswith("CQ-")
    assert ticket.status == "created"


def test_asana_create_ticket_assigns_selected_doctor_and_notes_context(monkeypatch) -> None:
    posted_payloads: list[dict] = []

    class SuccessResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "data": {
                    "gid": "task-123",
                    "permalink_url": "https://app.asana.com/0/project/task-123",
                }
            }

    class SuccessClient:
        def __init__(self, *args, **kwargs) -> None:
            _ = args, kwargs

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def post(self, *args, **kwargs):
            _ = args
            posted_payloads.append(kwargs["json"])
            return SuccessResponse()

    monkeypatch.setattr("nexus_ai.adapters.ticketing.httpx.Client", SuccessClient)

    adapter = AsanaTicketingAdapter()
    adapter.settings.asana_access_token = "token"
    adapter.settings.asana_project_gid = "project"
    adapter.settings.asana_assignee_gid = "fallback-user"

    ticket = adapter.create_review_ticket(
        patient_id=2,
        summary="Needs review for prescription update",
        case_type="doctor_review",
        doctor_asana_gid="doctor-user-123",
        doctor_name="Dr surgeon",
        urgency="high",
    )

    data = posted_payloads[0]["data"]
    assert ticket.ticket_id == "task-123"
    assert data["assignee"] == "doctor-user-123"
    assert data["projects"] == ["project"]
    assert "Doctor: Dr surgeon" in data["notes"]
    assert "Patient ID: 2" in data["notes"]
    assert "Urgency: high" in data["notes"]


def test_asana_list_workspace_users_falls_back_to_mock(monkeypatch) -> None:
    monkeypatch.setattr("nexus_ai.adapters.ticketing.httpx.Client", FailingClient)

    adapter = AsanaTicketingAdapter()
    adapter.settings.asana_access_token = "token"
    adapter.settings.asana_workspace_gid = "workspace-123"

    users = adapter.list_workspace_users()

    assert len(users) >= 1
    assert users[0]["gid"] == "mock-doctor-1"


def test_asana_list_workspace_users_reads_from_workspace_api(monkeypatch) -> None:
    requested_paths: list[str] = []

    class SuccessResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict:
            return {
                "data": [
                    {
                        "gid": "user-1",
                        "name": "Dr surgeon",
                        "email": "sreeshhb@gmail.com",
                    },
                    {
                        "gid": "user-2",
                        "name": "Dr Shaun",
                        "email": "shaun@example.com",
                    },
                ]
            }

    class SuccessClient:
        def __init__(self, *args, **kwargs) -> None:
            _ = args, kwargs

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, path, *args, **kwargs):
            _ = args, kwargs
            requested_paths.append(path)
            return SuccessResponse()

    monkeypatch.setattr("nexus_ai.adapters.ticketing.httpx.Client", SuccessClient)

    adapter = AsanaTicketingAdapter()
    adapter.settings.asana_access_token = "token"
    adapter.settings.asana_workspace_gid = "workspace-123"

    users = adapter.list_workspace_users()

    assert requested_paths == ["https://app.asana.com/api/1.0/workspaces/workspace-123/users"]
    assert users == [
        {"gid": "user-1", "name": "Dr surgeon", "email": "sreeshhb@gmail.com"},
        {"gid": "user-2", "name": "Dr Shaun", "email": "shaun@example.com"},
    ]
