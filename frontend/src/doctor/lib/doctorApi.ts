import { API_BASE_URL } from '../../shared/lib/api';

// For doctor module, allow a distinct backend URL if needed, default to same
export const DOCTOR_API_BASE_URL = import.meta.env.VITE_DOCTOR_API_BASE_URL ?? API_BASE_URL;

export async function runCell(code: string, prompt: string, sandboxId: string | null) {
  const response = await fetch(`${DOCTOR_API_BASE_URL}/api/v1/notebook/run-cell`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ code, prompt, sandboxId })
  });
  if (!response.ok) {
    const errText = await response.text();
    throw new Error(errText || 'Notebook cell run failed');
  }
  return response.json();
}

export async function chatNotebook(message: string, cellCode: string) {
  const response = await fetch(`${DOCTOR_API_BASE_URL}/api/v1/notebook/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, cell_code: cellCode })
  });
  if (!response.ok) {
    const errText = await response.text();
    throw new Error(errText || 'Notebook chat failed');
  }
  return response.json();
}

export async function uploadSandboxFile(file: File, sandboxId: string) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('sandboxId', sandboxId);
  const response = await fetch(`${DOCTOR_API_BASE_URL}/api/v1/notebook/upload`, {
    method: 'POST',
    body: formData
  });
  if (!response.ok) {
    const errText = await response.text();
    throw new Error(errText || 'File upload failed');
  }
  return response.json();
}

export async function explainOptions(question: string, options: string[]) {
  const response = await fetch(`${DOCTOR_API_BASE_URL}/api/v1/notebook/explain`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ question, options })
  });
  if (!response.ok) {
    const errText = await response.text();
    throw new Error(errText || 'Explain options failed');
  }
  return response.json();
}
