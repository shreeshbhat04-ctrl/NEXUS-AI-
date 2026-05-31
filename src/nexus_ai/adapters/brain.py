import asyncio
import os
import sys
from abc import ABC, abstractmethod
from pathlib import Path

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from nexus_ai.config import get_settings
from nexus_ai.db.session import SessionLocal
from nexus_ai.mcp.client_utils import extract_mcp_payload
from nexus_ai.services.brain import BrainCondition, BrainPatientProfile, BrainService


class BrainGateway(ABC):
    @abstractmethod
    def healthcheck(self) -> dict[str, str]:
        raise NotImplementedError

    @abstractmethod
    def get_patient_profile(self, patient_id: int) -> BrainPatientProfile | None:
        raise NotImplementedError

    @abstractmethod
    def get_relevant_conditions(self, patient_id: int) -> list[BrainCondition]:
        raise NotImplementedError


class DirectBrainGateway(BrainGateway):
    def __init__(self, brain_service: BrainService | None = None) -> None:
        self.brain_service = brain_service or BrainService()

    def healthcheck(self) -> dict[str, str]:
        with SessionLocal() as db:
            return self.brain_service.healthcheck(db)

    def get_patient_profile(self, patient_id: int) -> BrainPatientProfile | None:
        with SessionLocal() as db:
            return self.brain_service.get_patient_profile(db, patient_id)

    def get_relevant_conditions(self, patient_id: int) -> list[BrainCondition]:
        with SessionLocal() as db:
            return self.brain_service.get_relevant_conditions(db, patient_id)


class McpBrainGateway(BrainGateway):
    def __init__(self) -> None:
        self.settings = get_settings()
        self.repo_root = Path(__file__).resolve().parents[3]

    async def _call_tool(self, tool_name: str, arguments: dict) -> dict:
        command = sys.executable if self.settings.mcp_server_command == "python" else self.settings.mcp_server_command
        server_params = StdioServerParameters(
            command=command,
            args=self.settings.mcp_server_arg_list,
            cwd=str(self.repo_root),
            env=os.environ.copy(),
        )
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments=arguments)
                return extract_mcp_payload(result)

    def _run_sync(self, coro) -> dict:
        import concurrent.futures
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            return pool.submit(asyncio.run, coro).result()

    def healthcheck(self) -> dict[str, str]:
        return self._run_sync(self._call_tool("brain_healthcheck", {}))

    def get_patient_profile(self, patient_id: int) -> BrainPatientProfile | None:
        payload = self._run_sync(self._call_tool("brain_get_patient_profile", {"patient_id": patient_id}))
        profile = payload.get("profile")
        if profile is None:
            return None
        return BrainPatientProfile(**profile)

    def get_relevant_conditions(self, patient_id: int) -> list[BrainCondition]:
        payload = self._run_sync(self._call_tool("brain_get_relevant_conditions", {"patient_id": patient_id}))
        return [BrainCondition(**item) for item in payload.get("conditions", [])]


def build_brain_gateway() -> BrainGateway:
    settings = get_settings()
    if settings.brain_gateway_mode == "mcp":
        return McpBrainGateway()
    return DirectBrainGateway()
