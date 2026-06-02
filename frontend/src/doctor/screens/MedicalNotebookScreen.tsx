import { useState } from "react";
import Notebook from "../components/notebook/Notebook";
import WorkspaceSidebar from "../components/notebook/WorkspaceSidebar";

export default function MedicalNotebookScreen() {
  const [sandboxId, setSandboxId] = useState<string | null>(null);

  return (
    <div style={{ display: 'flex', gap: '1.5rem', minHeight: 'calc(100vh - 8rem)' }}>
      {/* Workspace Sidebar */}
      <div style={{ flexShrink: 0 }}>
        <WorkspaceSidebar sandboxId={sandboxId} />
      </div>
      
      {/* Notebook Editor */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <Notebook sandboxId={sandboxId} setSandboxId={setSandboxId} />
      </div>
    </div>
  );
}
