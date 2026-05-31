from pprint import pprint

import httpx

from nexus_ai.config import get_settings


def main() -> None:
    settings = get_settings()
    if not settings.asana_access_token:
        raise SystemExit("ASANA_ACCESS_TOKEN is not set.")

    headers = {
        "Authorization": f"Bearer {settings.asana_access_token}",
        "Accept": "application/json",
    }

    with httpx.Client(timeout=20.0) as client:
        me = client.get("https://app.asana.com/api/1.0/users/me", headers=headers)
        me.raise_for_status()
        print("ME")
        pprint(me.json()["data"])

        workspaces = client.get("https://app.asana.com/api/1.0/workspaces", headers=headers)
        workspaces.raise_for_status()
        print("WORKSPACES")
        pprint(workspaces.json()["data"])

        if settings.asana_workspace_gid:
            projects = client.get(
                f"https://app.asana.com/api/1.0/workspaces/{settings.asana_workspace_gid}/projects",
                headers=headers,
            )
            projects.raise_for_status()
            print("PROJECTS")
            pprint(projects.json()["data"])


if __name__ == "__main__":
    main()
