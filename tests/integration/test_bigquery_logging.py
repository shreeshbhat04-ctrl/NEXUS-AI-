from pprint import pprint

from nexus_ai.agents.integrations import IntegrationAgent


def main() -> None:
    agent = IntegrationAgent()
    result = agent.log_integration_event(
        "manual_bigquery_test",
        {
            "source": "script",
            "status": "ok",
        },
    )
    pprint(result)


if __name__ == "__main__":
    main()
