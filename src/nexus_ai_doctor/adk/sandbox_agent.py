import json
from google.adk.agents import Agent
from google.adk.tools.agent_tool import AgentTool
from e2b_code_interpreter import Sandbox

from nexus_ai.config import get_settings

def execute_sandbox_code(python_code: str) -> str:
    """Execute python code in a secure sandbox and return the output.
    
    You can use this tool to perform complex data analysis with pandas,
    generate charts, or interact with APIs.
    
    If interacting with Google Workspace, you have access to the workspace_cli module.
    """
    settings = get_settings()
    
    # Optional timeout and other settings could be added
    try:
        # Create a new sandbox
        # Note: requires E2B_API_KEY environment variable
        with Sandbox() as sandbox:
            
            # Setup workspace_cli for the sandbox if needed
            with open("c:/Users/shree/project/nexus_ai/src/nexus_ai_doctor/tools/workspace_cli.py", "r") as f:
                cli_code = f.read()
                
            sandbox.files.write("/home/user/workspace_cli.py", cli_code)
            
            # Execute the user's code
            execution = sandbox.run_code(python_code)
            
            result = {
                "text": execution.text,
                "error": execution.error.model_dump() if execution.error else None,
            }
            return json.dumps(result)
            
    except Exception as e:
        return json.dumps({"error": str(e)})

sandbox_agent = Agent(
    model=get_settings().adk_model,
    name="nexus_ai_sandbox_agent",
    description="Agent for writing and executing code securely in an E2B sandbox. Good for data analysis, complex math, or programmatic workspace actions.",
    instruction=(
        "You are the nexus_ai Sandbox Agent. You write Python code to solve complex problems "
        "and execute it using the execute_sandbox_code tool.\n\n"
        "You can use pandas, numpy, and other data science tools. "
        "If you need to interact with Google Calendar or Gmail, use the provided `workspace_cli` module.\n"
        "Example:\n"
        "from workspace_cli import WorkspaceCLI\n"
        "cli = WorkspaceCLI()\n"
        "events = cli.list_calendar_events(calendar_id='primary')\n"
    ),
    tools=[execute_sandbox_code]
)
