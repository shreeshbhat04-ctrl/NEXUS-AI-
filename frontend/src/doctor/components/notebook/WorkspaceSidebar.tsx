import { useState } from "react";
import { File, Upload, Loader2, FolderOpen } from "lucide-react";
import { uploadSandboxFile } from "../../lib/doctorApi";
import "./notebook.css";

export default function WorkspaceSidebar({ sandboxId }: { sandboxId: string | null }) {
  const [files, setFiles] = useState<{name: string, path: string}[]>([]);
  const [isUploading, setIsUploading] = useState(false);

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0 || !sandboxId) return;
    
    const file = e.target.files[0];
    setIsUploading(true);
    
    try {
      const data = await uploadSandboxFile(file, sandboxId);
      if (data.success) {
        setFiles(prev => [...prev, { name: file.name, path: data.path }]);
      } else {
        alert("Upload failed: " + data.error);
      }
    } catch (err: any) {
      alert("Error uploading file: " + err.message);
    } finally {
      setIsUploading(false);
      e.target.value = ''; // reset input
    }
  };

  return (
    <div className="workspace-sidebar">
      <div className="sidebar-header">
        <FolderOpen size={18} />
        <h2>Workspace</h2>
      </div>

      {!sandboxId ? (
        <div className="sidebar-info-card">
          Run your first cell to initialize sandbox and enable file uploads.
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <label className="upload-zone">
            {isUploading ? <Loader2 size={24} className="animate-spin" style={{ marginBottom: '0.5rem' }} /> : <Upload size={24} style={{ marginBottom: '0.5rem' }} />}
            <span style={{ fontSize: '0.875rem', fontWeight: 500 }}>{isUploading ? "Uploading..." : "Upload File"}</span>
            <input type="file" style={{ display: 'none' }} onChange={handleFileUpload} disabled={isUploading} />
          </label>

          <div style={{ marginTop: '1rem' }}>
            <h3 className="files-section-title">Sandbox Files</h3>
            {files.length === 0 ? (
              <div style={{ fontSize: '0.875rem', color: '#94a3b8', fontStyle: 'italic' }}>No files uploaded yet.</div>
            ) : (
              <ul style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem', listStyle: 'none', padding: 0, margin: 0 }}>
                {files.map((f, i) => (
                  <li key={i} className="file-item">
                    <File size={16} style={{ color: '#94a3b8', flexShrink: 0 }} />
                    <span className="file-item-name" title={f.path}>{f.name}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
