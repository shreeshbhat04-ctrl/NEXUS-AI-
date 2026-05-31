import asyncio
import json
import os
from pathlib import Path
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from nexus_ai.agents.intake import IntakeAgent
from nexus_ai.api.models import ConditionInput, PatientIntakeRequest
from nexus_ai.db.bootstrap import init_database
from nexus_ai.db.session import SessionLocal
from nexus_ai.mcp.client_utils import extract_mcp_payload


def seed_demo_patient() -> int:
    init_database()
    with SessionLocal() as db:
        patient = IntakeAgent().intake_patient(
            db,
            PatientIntakeRequest(
                full_name="MCP Demo Patient",
                preferred_language="en",
                active_conditions=[
                    ConditionInput(name="IBS", condition_type="chronic"),
                ],
            ),
        )
        return patient.id


async def main() -> None:
    patient_id = seed_demo_patient()
    repo_root = Path(__file__).resolve().parents[1]
    server_params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "nexus_ai.mcp.server"],
        cwd=str(repo_root),
        env=os.environ.copy(),
    )

    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("TOOLS", [tool.name for tool in tools.tools])

            ping_result = await session.call_tool("ping", arguments={})
            print("PING", json.dumps(extract_mcp_payload(ping_result), indent=2))

            brain_result = await session.call_tool("brain_healthcheck", arguments={})
            print("BRAIN", json.dumps(extract_mcp_payload(brain_result), indent=2))

            profile_result = await session.call_tool(
                "brain_get_patient_profile",
                arguments={"patient_id": patient_id},
            )
            print("PROFILE", json.dumps(extract_mcp_payload(profile_result), indent=2))

            conditions_result = await session.call_tool(
                "brain_get_relevant_conditions",
                arguments={"patient_id": patient_id},
            )
            print("CONDITIONS", json.dumps(extract_mcp_payload(conditions_result), indent=2))

            emergency_result = await session.call_tool(
                "check_emergency",
                arguments={"text": "Patient says chest pain started 10 minutes ago."},
            )
            print("EMERGENCY", json.dumps(extract_mcp_payload(emergency_result), indent=2))


if __name__ == "__main__":
    asyncio.run(main())
