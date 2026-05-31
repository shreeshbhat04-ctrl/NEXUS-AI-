import asyncio
import os

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from nexus_ai.adk.agent import root_agent


async def main() -> None:
    if not os.environ.get("GOOGLE_API_KEY"):
        print("GOOGLE_API_KEY is not set. ADK wiring is present, but model-backed execution is skipped.")
        return

    session_service = InMemorySessionService()
    app_name = "nexus_ai"
    user_id = "local-dev"
    session = await session_service.create_session(app_name=app_name, user_id=user_id)
    runner = Runner(agent=root_agent, app_name=app_name, session_service=session_service)

    content = Content(role="user", parts=[Part(text="Use your tools to verify the MCP server is alive.")])
    async for event in runner.run_async(user_id=user_id, session_id=session.id, new_message=content):
        if getattr(event, "content", None):
            print(event.content)


if __name__ == "__main__":
    asyncio.run(main())
