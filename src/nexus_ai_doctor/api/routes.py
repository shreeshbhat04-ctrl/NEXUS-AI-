from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat_with_doctor_agent(request: ChatRequest):
    from nexus_ai_doctor.adk.agent import root_doctor_agent
    
    # We would integrate with the actual user context here
    response = await root_doctor_agent.generate_response(request.message)
    return {"response": response}

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "nexus_ai_doctor"}
