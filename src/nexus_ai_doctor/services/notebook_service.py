import os
import logging
from e2b_code_interpreter import Sandbox

logger = logging.getLogger(__name__)

class NotebookService:
    def __init__(self):
        self.api_key = os.environ.get("E2B_API_KEY")

    def execute_code(self, code: str, sandbox_id: str = None) -> dict:
        try:
            if sandbox_id:
                logger.info(f"Connecting to E2B sandbox: {sandbox_id}")
                sandbox = Sandbox.connect(sandbox_id)
            else:
                logger.info("Creating new E2B sandbox...")
                sandbox = Sandbox(api_key=self.api_key)
                
            logger.info(f"Running code in sandbox: {sandbox.sandbox_id}")
            result = sandbox.run_code(code)
            
            # Format logs
            stdout_logs = []
            stderr_logs = []
            if result.logs:
                stdout_logs = [log.line for log in result.logs.stdout]
                stderr_logs = [log.line for log in result.logs.stderr]
                
            # Format results
            formatted_results = []
            if result.results:
                for r in result.results:
                    res_dict = {}
                    if hasattr(r, 'png') and r.png:
                        res_dict['png'] = r.png
                    if hasattr(r, 'jpeg') and r.jpeg:
                        res_dict['jpeg'] = r.jpeg
                    if hasattr(r, 'svg') and r.svg:
                        res_dict['svg'] = r.svg
                    if hasattr(r, 'html') and r.html:
                        res_dict['html'] = r.html
                    if res_dict:
                        formatted_results.append(res_dict)

            # Format error
            formatted_error = None
            if result.error:
                formatted_error = {
                    "name": result.error.name,
                    "value": result.error.value,
                    "traceback": result.error.traceback
                }
                
            return {
                "status": "success",
                "result": {
                    "text": result.text,
                    "logs": {
                        "stdout": stdout_logs,
                        "stderr": stderr_logs
                    },
                    "results": formatted_results,
                    "error": formatted_error
                },
                "sandboxId": sandbox.sandbox_id
            }
        except Exception as e:
            logger.error(f"E2B execution failed: {e}")
            return {
                "status": "error",
                "errors": str(e),
                "sandboxId": sandbox_id
            }

    def upload_file(self, file_content: bytes, filename: str, sandbox_id: str) -> dict:
        try:
            logger.info(f"Connecting to E2B sandbox {sandbox_id} to upload file {filename}")
            sandbox = Sandbox.connect(sandbox_id)
            
            remote_path = f"/home/user/{filename}"
            # Write file content to E2B sandbox filesystem
            sandbox.files.write(remote_path, file_content)
            
            return {
                "success": True,
                "path": remote_path
            }
        except Exception as e:
            logger.error(f"E2B upload failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
