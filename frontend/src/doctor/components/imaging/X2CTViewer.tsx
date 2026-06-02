import { useState } from "react";
import { UploadCloud, Loader2, Play } from "lucide-react";
import { reconstructImaging } from "../../lib/doctorApi";

const OHIF_URL = import.meta.env.VITE_OHIF_URL ?? "http://localhost:3001";

export default function X2CTViewer() {
  const [apFile, setApFile] = useState<File | null>(null);
  const [latFile, setLatFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [dicomUrl, setDicomUrl] = useState<string | null>(null);

  const handleRunReconstruction = async () => {
    if (!apFile || !latFile) return;
    
    setIsUploading(true);
    
    try {
      const data = await reconstructImaging(apFile, latFile);
      if (data.status === "success") {
        setDicomUrl(data.dicom_url);
      } else {
        alert("Reconstruction failed.");
      }
    } catch (error: any) {
      console.error(error);
      alert("Error communicating with doctor backend reconstruction service: " + error.message);
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div style={{ maxWidth: '72rem', margin: '0 auto', display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      <div 
        style={{
          backgroundColor: '#ffffff',
          padding: '1.5rem',
          borderRadius: '1rem',
          boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
          border: '1px solid #e2e8f0'
        }}
      >
        <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', margin: '0 0 0.5rem 0' }}>X2CT 3D Reconstruction</h2>
        <p style={{ color: '#64748b', fontSize: '0.9rem', margin: '0 0 1.5rem 0' }}>
          Upload Anteroposterior (Front) and Lateral (Side) X-Ray images. The AI will reconstruct a 3D CT volume and display it in the embedded clinical-grade OHIF Viewer.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>
          <div 
            style={{
              border: '2px dashed #cbd5e1',
              borderRadius: '0.75rem',
              padding: '1.5rem',
              textAlign: 'center',
              backgroundColor: '#f8fafc',
              cursor: 'pointer'
            }}
          >
            <UploadCloud style={{ margin: '0 auto 0.5rem auto', color: '#94a3b8' }} size={32} />
            <p style={{ fontWeight: 500, fontSize: '0.95rem', margin: '0 0 0.5rem 0' }}>AP X-Ray (Front)</p>
            <input 
              type="file" 
              accept="image/*" 
              style={{
                fontSize: '0.85rem',
                color: '#64748b',
                maxWidth: '100%'
              }}
              onChange={(e) => setApFile(e.target.files?.[0] || null)}
            />
          </div>
          <div 
            style={{
              border: '2px dashed #cbd5e1',
              borderRadius: '0.75rem',
              padding: '1.5rem',
              textAlign: 'center',
              backgroundColor: '#f8fafc',
              cursor: 'pointer'
            }}
          >
            <UploadCloud style={{ margin: '0 auto 0.5rem auto', color: '#94a3b8' }} size={32} />
            <p style={{ fontWeight: 500, fontSize: '0.95rem', margin: '0 0 0.5rem 0' }}>Lateral X-Ray (Side)</p>
            <input 
              type="file" 
              accept="image/*" 
              style={{
                fontSize: '0.85rem',
                color: '#64748b',
                maxWidth: '100%'
              }}
              onChange={(e) => setLatFile(e.target.files?.[0] || null)}
            />
          </div>
        </div>

        <button 
          onClick={handleRunReconstruction}
          disabled={!apFile || !latFile || isUploading}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '100%',
            padding: '0.75rem',
            borderRadius: '0.75rem',
            fontWeight: 500,
            border: 'none',
            cursor: (!apFile || !latFile || isUploading) ? 'not-allowed' : 'pointer',
            backgroundColor: (!apFile || !latFile || isUploading) ? '#e2e8f0' : '#2563eb',
            color: (!apFile || !latFile || isUploading) ? '#94a3b8' : '#ffffff',
            transition: 'background-color 0.2s'
          }}
        >
          {isUploading ? <Loader2 className="animate-spin" style={{ marginRight: '0.5rem' }} size={20} /> : <Play style={{ marginRight: '0.5rem' }} size={20} />}
          {isUploading ? "Reconstructing 3D Volume..." : "Run Reconstruction"}
        </button>
      </div>

      {dicomUrl && (
        <div 
          style={{
            backgroundColor: '#ffffff',
            borderRadius: '1rem',
            boxShadow: '0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px 0 rgba(0, 0, 0, 0.06)',
            border: '1px solid #e2e8f0',
            overflow: 'hidden',
            display: 'flex',
            flexDirection: 'column',
            height: '600px'
          }}
        >
          <div 
            style={{
              backgroundColor: '#0f172a',
              padding: '0.75rem 1rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'between',
              color: '#ffffff',
              flexShrink: 0
            }}
          >
            <h3 style={{ fontSize: '0.95rem', fontWeight: 600, margin: 0, flex: 1 }}>OHIF Viewer (Clinical Grade)</h3>
            <span style={{ fontSize: '0.7rem', backgroundColor: '#1e293b', padding: '0.25rem 0.5rem', borderRadius: '0.25rem' }}>Source: {dicomUrl}</span>
          </div>
          <iframe 
            style={{
              width: '100%',
              flex: 1,
              backgroundColor: '#000000',
              border: 'none'
            }}
            src={`${OHIF_URL}/viewer?url=${encodeURIComponent(dicomUrl)}`}
            title="OHIF Viewer"
            allowFullScreen
          />
        </div>
      )}
    </div>
  );
}
