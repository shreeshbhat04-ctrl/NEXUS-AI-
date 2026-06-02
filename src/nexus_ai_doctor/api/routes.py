import os
import time
import logging
from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from pydantic import BaseModel
from typing import Optional, List

from nexus_ai_doctor.services.notebook_service import NotebookService
from nexus_ai_doctor.services.gemini_copilot import GeminiCopilot
from nexus_ai_doctor.services.imaging_service import ImagingService

logger = logging.getLogger(__name__)
router = APIRouter()

# Initialize services
notebook_service = NotebookService()
gemini_copilot = GeminiCopilot()
imaging_service = ImagingService()

class ChatRequest(BaseModel):
    message: str

@router.post("/chat")
async def chat_with_doctor_agent(request: ChatRequest):
    from nexus_ai_doctor.adk.agent import root_doctor_agent
    response = await root_doctor_agent.generate_response(request.message)
    return {"response": response}

@router.get("/health")
async def health_check():
    return {"status": "ok", "service": "nexus_ai_doctor"}

# --- Medical AI Notebook Endpoints ---

class RunCellRequest(BaseModel):
    code: Optional[str] = ""
    prompt: Optional[str] = ""
    sandboxId: Optional[str] = None

@router.post("/notebook/run-cell")
async def run_cell(req: RunCellRequest):
    start_time = time.time()
    code = req.code.strip() if req.code else ""
    
    # If code is empty but prompt is provided, generate using Gemini Copilot
    if not code:
        if not req.prompt or not req.prompt.strip():
            raise HTTPException(status_code=400, detail="Missing code or prompt")
            
        llm_response = await gemini_copilot.generate_code_or_clarify(req.prompt)
        
        if llm_response.get("status") == "AMBIGUOUS":
            return {
                "status": "AMBIGUOUS",
                "question": llm_response.get("question"),
                "options": llm_response.get("options"),
                "sandboxId": req.sandboxId
            }
            
        code = llm_response.get("code", "")
        if not code:
            raise HTTPException(status_code=500, detail="Failed to generate code")

    # Execute code in E2B sandbox
    execution_result = notebook_service.execute_code(code, req.sandboxId)
    execution_time = time.time() - start_time
    
    if execution_result.get("status") == "error":
        return {
            "status": "EXECUTABLE",
            "code": code,
            "errors": execution_result.get("errors"),
            "sandboxId": req.sandboxId,
            "execution_time": execution_time
        }
        
    return {
        "status": "EXECUTABLE",
        "code": code,
        "result": execution_result.get("result"),
        "sandboxId": execution_result.get("sandboxId"),
        "execution_time": execution_time
    }

class NotebookChatRequest(BaseModel):
    message: str
    cell_code: str

@router.post("/notebook/chat")
async def chat_notebook(req: NotebookChatRequest):
    # Contextual chat in notebook
    prompt = f"The user is working in a medical AI notebook. Here is their current cell code:\n```python\n{req.cell_code}\n```\nUser Message: {req.message}\nProvide a helpful response or updated code."
    
    if not gemini_copilot.client:
        return {"response": "Error: Gemini API client not initialized. Check GEMINI_API_KEY environment variable."}
        
    try:
        response = await gemini_copilot.client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        return {"response": response.text}
    except Exception as e:
        logger.error(f"Error in notebook chat: {e}")
        return {"response": f"Error calling Gemini API: {str(e)}"}

class ExplainOptionsRequest(BaseModel):
    question: str
    options: List[str]

@router.post("/notebook/explain")
async def explain_options(req: ExplainOptionsRequest):
    mermaid_code = await gemini_copilot.generate_mermaid_diagram(req.question, req.options)
    return {"mermaid": mermaid_code}

@router.post("/notebook/upload")
async def upload_file_to_sandbox(
    file: UploadFile = File(...),
    sandboxId: str = Form(...)
):
    try:
        file_content = await file.read()
        res = notebook_service.upload_file(file_content, file.filename, sandboxId)
        return res
    except Exception as e:
        logger.error(f"Failed to upload file to sandbox: {e}")
        return {"success": False, "error": str(e)}

# --- 3D Imaging Reconstruction Endpoints ---

@router.post("/imaging/reconstruct")
async def reconstruct_3d(
    ap_xray: UploadFile = File(...),
    lat_xray: UploadFile = File(...)
):
    try:
        ap_bytes = await ap_xray.read()
        lat_bytes = await lat_xray.read()
        
        # Save to static directory for serving to OHIF viewer
        study_dir = os.path.join("static", "dicoms", "study_1")
        imaging_service.reconstruct_ct(ap_bytes, lat_bytes, study_dir)
        
        # Check if there is a custom base URL configured, otherwise construct local
        host_url = os.environ.get("DOCTOR_BACKEND_URL", "http://localhost:8000")
        dicom_url = f"{host_url}/static/dicoms/study_1"
        
        return {"status": "success", "dicom_url": dicom_url}
    except Exception as e:
        logger.error(f"Failed to run reconstruction: {e}")
        raise HTTPException(status_code=500, detail=str(e))
